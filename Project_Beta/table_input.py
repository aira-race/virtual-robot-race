# table_input.py
# Sends drive/steer commands read from a CSV file to Unity via WebSocket
# Updated for steer-type control (Drive_Torque, Steer_Angle)

import pandas as pd
import asyncio
import websocket_server
import os
from threading import Event

start_event = Event()  # Trigger event to begin sending

# CSV file path
INPUT_CSV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "table_input.csv")

csv_loaded = False
df = None  # DataFrame to hold CSV content

# Latest command cache for get_latest_command()
_latest_drive = 0.0
_latest_steer = 0.0

def get_latest_command():
    """Return the latest control command in the expected format."""
    return {
        "type": "control",
        "robot_id": "R1",
        "driveTorque": _latest_drive,
        "steerAngle": _latest_steer,
    }

def start_csv_replay():
    """Called once to trigger CSV replay"""
    print("[TableInput] Start signal received.")
    start_event.set()

async def run_table_input_loop(stop_event):
    """Main loop to read and send drive/steer values from CSV"""
    global df, csv_loaded, _latest_drive, _latest_steer

    if not os.path.exists(INPUT_CSV_FILE):
        print(f"[TableInput] CSV file not found: {INPUT_CSV_FILE}")
        return

    if not csv_loaded:
        df = pd.read_csv(INPUT_CSV_FILE)
        print(f"[TableInput] Loaded {len(df)} command rows from CSV.")
        csv_loaded = True

    print("[TableInput] Waiting for start event...")
    await asyncio.to_thread(start_event.wait)  # Wait non-blocking

    print("[TableInput] Start event detected. Begin sending drive/steer commands.")

    for _, row in df.iterrows():
        if stop_event.is_set():
            break

        # Read drive_torque and steer_angle from CSV
        drive = float(row.get("Drive_Torque", 0.0))
        steer = float(row.get("Steer_Angle", 0.0))

        # Update cache
        _latest_drive = drive
        _latest_steer = steer

        # Send command to Unity
        await websocket_server.send_control_command_async(drive, steer)
        await asyncio.sleep(0.05)  # Send at 20 Hz (50 ms interval)

    print("[TableInput] CSV replay completed.")
