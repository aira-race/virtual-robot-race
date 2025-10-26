# websocket_server.py
# WebSocket server that talks to Unity:
# - Sends torque commands at 20 Hz (every 50 ms)
# - Receives images (binary) and per-tick metadata (JSON)
# - On race end, receives final race metadata JSON (no images)
#
# Protocol (from Unity):
#   Per tick (50 ms):
#     1) binary: JPG bytes (optional; may be missing on some ticks)
#     2) text:   JSON  {"type":"data","tick":..., "utc_ms":..., "filename":"frame_000123.jpg",
#                       "soc":..., "status":..., "leftTorque":..., "rightTorque":...}
#   On race end:
#     text: final race JSON (DataLogger summary) -> saved as metadata.csv by DataManager
#
# This server:
#   - Buffers the most recent image bytes (no backlog)
#   - Saves the image when the subsequent JSON arrives (so filenames match)
#   - Appends a simple frames_map.csv per tick (optional but useful for audits)
#   - Keeps torque sender and receiver tasks tracked for graceful shutdown

import asyncio
import json
import os
from pathlib import Path
from threading import Event

import websockets
import config

# Data layer
# Expect DataManager with:
#   start_new_run() -> (run_dir, images_dir)
#   save_image_bytes(path: Path, data: bytes)
#   append_frame_map(tick, utc_ms, filename, soc, status, left_tq, right_tq)
#   save_metadata_csv_from_unity_json(obj: dict)
#   flush_frame_map()
from data_manager import DataManager, BASE_DIR
dm = DataManager(BASE_DIR)
run_dir, images_dir = dm.start_new_run()

# Choose control input module
if config.MODE == "keyboard":
    import keyboard_input as control_module
elif config.MODE == "table":
    import table_input as control_module
elif config.MODE == "rule_based":
    import rule_based_input as control_module
elif config.MODE == "ai":
    import inference_input as control_module
else:
    raise ValueError(f"[Server] Unknown control mode: {config.MODE}")

# ---- Globals ---------------------------------------------------------------

TORQUE_FILE = os.path.join("data_interactive", "latest_torque.txt")

frame_received_event = Event()              # fire once when the first frame is saved
shutdown_event = asyncio.Event()            # global shutdown signal
connected_websocket = None                  # current client connection
_bg_tasks: set[asyncio.Task] = set()        # track background tasks
_ws_server = None                           # server handle

# Data session objects
_dm: DataManager | None = None
_run_dir: Path | None = None
_images_dir: Path | None = None


def _track(task: asyncio.Task) -> asyncio.Task:
    """Register a background task so we can cancel/await it on shutdown."""
    _bg_tasks.add(task)
    task.add_done_callback(_bg_tasks.discard)
    return task


# ---- Utility ---------------------------------------------------------------

def write_latest_torque(left: float, right: float) -> None:
    """Write the latest torque to a file so external tools can read it."""
    try:
        os.makedirs(os.path.dirname(TORQUE_FILE), exist_ok=True)
        with open(TORQUE_FILE, "w", encoding="utf-8") as f:
            f.write(f"{left:.4f},{right:.4f}")
    except Exception as e:
        print(f"[Server] Failed to write torque to file: {e}")



# ---- Loops -----------------------------------------------------------------

async def send_torque_data(websocket: websockets.WebSocketServerProtocol) -> None:
    """Send control command to Unity every 50 ms (20 Hz)."""
    print("[Server] Starting control-data sender...")
    try:
        while not shutdown_event.is_set():
            await asyncio.sleep(0.05)

            msg = None
            if hasattr(control_module, "get_latest_command"):
                try:
                    msg = control_module.get_latest_command()
                    # 必須の保険
                    msg.setdefault("type", "control")
                    msg.setdefault("robot_id", "R1")
                except Exception as e:
                    print(f"[Server] get_latest_command() failed: {e}")

            if msg is None:
                # 後方互換（存在するなら）：左右→drive、steer=0
                lt = float(getattr(control_module, "leftTorque", 0.0))
                rt = float(getattr(control_module, "rightTorque", 0.0))
                msg = {
                    "type": "control",
                    "robot_id": "R1",
                    "driveTorque": 0.5 * (lt + rt),
                    "steerAngle": 0.0,
                }

            try:
                await websocket.send(json.dumps(msg))
                # ログが多ければコメントアウト：
                # print(f"[Server] Sent control: {msg}")
            except websockets.exceptions.ConnectionClosed:
                print("[Server] WebSocket closed. Stopping sender.")
                break
    except asyncio.CancelledError:
        pass
    finally:
        print("[Server] Control-data sender exited.")


async def receive_stream(websocket: websockets.WebSocketServerProtocol) -> None:
    """Receive binary images and JSON metadata from Unity."""
    global _dm, _images_dir
    print("[Server] Ready to receive data from Unity...")

    last_image_buf: bytes | None = None
    first_frame_saved = False

    try:
        async for message in websocket:
            if isinstance(message, (bytes, bytearray)):
                last_image_buf = bytes(message)
                continue

            # Text = JSON
            try:
                data = json.loads(message)
            except Exception as e:
                print(f"[Server] Ignoring non-JSON text: {e}")
                continue

            mtype = data.get("type", "")

            if mtype == "data":
                tick = data.get("tick")
                utc_ms = data.get("utc_ms")
                filename = data.get("filename") or (f"frame_{int(tick):06d}.jpg" if tick is not None else "no_image")
                # 任意でdrive/steerを拾いたければここで取り出す
                # drive = data.get("driveTorque"); steer = data.get("steerAngle")

                if last_image_buf is not None and filename != "no_image":
                    try:
                        _dm.save_image_bytes(_images_dir / filename, last_image_buf)
                        last_image_buf = None
                        if not first_frame_saved:
                            first_frame_saved = True
                            frame_received_event.set()
                            print("[Server] First frame saved.")
                    except Exception as e:
                        print(f"[Server] Failed to save image {filename}: {e}")

            elif mtype in ("race_data", "RaceData"):
                try:
                    print("[Server] Received race metadata.")
                    payload = data.get("payload", data)
                    if isinstance(payload, str):
                        try:
                            payload = json.loads(payload)
                        except Exception:
                            pass
                    _dm.save_metadata_csv_from_unity_json(payload)
                except Exception as e:
                    print(f"[Server] Failed to save final race metadata: {e}")
                break  # ← 本当にレース終了の時だけ抜ける

            elif mtype == "connection" and data.get("message") == "RaceEnd":
                break  # 明示終了

            else:
                # type 未指定/未知 → 無視して継続
                pass

    except websockets.exceptions.ConnectionClosed:
        print("[Server] Client disconnected.")
    except asyncio.CancelledError:
        pass
    finally:
        print("[Server] Image/SOC reception stopped.")

# ---- Connection handler ----------------------------------------------------

async def handler(websocket: websockets.WebSocketServerProtocol, stop_event: Event) -> None:
    """Handle a new client connection."""
    global connected_websocket, _dm, _run_dir, _images_dir

    connected_websocket = websocket
    frame_received_event.clear()
    print("[Server] Client connected.")

    # ★ keyboard listener（あれば起動）
    try:
        if hasattr(control_module, "start_listener"):
            control_module.start_listener()
    except Exception as e:
        print(f"[Server] Keyboard listener start failed: {e}")

    # Start a new run directory
    try:
        base_dir = Path(__file__).parent
        _dm = DataManager(base_dir=base_dir)
        _run_dir, _images_dir = _dm.start_new_run()
    except Exception as e:
        print(f"[Server] DataManager init failed: {e}")
        _dm = None; _run_dir = None; _images_dir = None

    # Handshake（既存のまま）
    try:
        handshake = {
            "type": "connection",
            "status": "success",
            "name": config.NAME,
            "mode": config.MODE,
            "mode_num": config.MODE_NUM,
            "race_flag": config.RACE_FLAG,
        }
        await websocket.send(json.dumps(handshake))
        print(f"[Server] Sent handshake → name={config.NAME}, mode={config.MODE}, race_flag={config.RACE_FLAG}")
    except websockets.exceptions.ConnectionClosed:
        print("[Server] Connection failed during handshake.")
        return

    # Start background loops
    send_task = _track(asyncio.create_task(send_torque_data(websocket)))
    recv_task = _track(asyncio.create_task(receive_stream(websocket)))

    try:
        await recv_task
    finally:
        print("[Server] Connection closed (handler cleanup).")

        for t in (send_task, recv_task):
            if not t.done():
                t.cancel()
        await asyncio.gather(send_task, recv_task, return_exceptions=True)

        # ★ keyboard listener停止
        try:
            if hasattr(control_module, "stop_listener"):
                control_module.stop_listener()
        except Exception as e:
            print(f"[Server] Keyboard listener stop failed: {e}")

        shutdown_event.set()
        stop_event.set()
        connected_websocket = None


# ---- Public API for main.py ------------------------------------------------

async def start_server(stop_event: Event) -> None:
    """Launch the WebSocket server and wait until stop_event is set."""
    global _ws_server

    host, port = config.HOST, config.PORT
    _ws_server = await websockets.serve(lambda ws: handler(ws, stop_event), host, port)
    print(f"[Server] WebSocket server running at ws://{host}:{port}")

    # Wait until the blocking threading.Event is set (from main.py)
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, stop_event.wait)


async def shutdown_server() -> None:
    """Gracefully stop server & background tasks (no pending warnings)."""
    global _ws_server

    print("[Server] Shutting down server...")

    # 1) Cancel background tasks
    if _bg_tasks:
        for t in list(_bg_tasks):
            if not t.done():
                t.cancel()
        await asyncio.gather(*list(_bg_tasks), return_exceptions=True)
        _bg_tasks.clear()

    # 2) Close active connection (best-effort)
    try:
        if connected_websocket and not connected_websocket.closed:
            await connected_websocket.close()
    except Exception:
        pass

    # 3) Close server
    if _ws_server is not None:
        _ws_server.close()
        try:
            await _ws_server.wait_closed()
        except Exception:
            pass
        _ws_server = None
        print("[Server] WebSocket server closed.")


async def send_race_end_signal() -> None:
    """Send a 'RaceEnd' command to Unity (optional helper)."""
    if connected_websocket:
        try:
            message = json.dumps({
                "type": "connection",
                "message": "RaceEnd",
                "name": config.NAME,
                "mode": config.MODE,
                "race_flag": config.RACE_FLAG,
            })
            await connected_websocket.send(message)
            print(f"[Server] Sent RaceEnd signal → name={config.NAME}, mode={config.MODE}")
        except Exception as e:
            print(f"[Server] Failed to send RaceEnd: {e}")
    else:
        print("[Server] No client connected to send RaceEnd.")


# 置換：send_control_command_async()
async def send_control_command_async(drive: float, steer: float, robot_id: str = "R1") -> None:
    """Send a manual drive+steer command (used by 'table' etc.)."""
    if connected_websocket:
        try:
            message = json.dumps({
                "type": "control",
                "robot_id": robot_id,
                "driveTorque": float(drive),
                "steerAngle": float(steer),
            })
            await connected_websocket.send(message)
            print(f"[Server] Sent manual control → id={robot_id}, drive={drive:.3f}, steer={steer:.3f}")
        except Exception as e:
            print(f"[Server] Error sending control: {e}")
    else:
        print("[Server] No connected client.")

