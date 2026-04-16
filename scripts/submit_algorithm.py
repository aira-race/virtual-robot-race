# submit_algorithm.py
# ============================================================
# Algorithm Submission Tool for aira - Beta 1.7
# ============================================================
# USAGE:
#   python scripts/submit_algorithm.py
#
# Files collected automatically:
#   - config.txt
#   - Robot{N}/*.py  (root level)
#   - Robot{N}/rule_based_algorithms/*.py
#   - Robot{N}/models/model.pth   (MODE_NUM=4 only)
#   - Robot{N}/table_input.csv    (MODE_NUM=2 only)
#
# Excluded:
#   - ai_training/, experiments/, training_data/, debug/, __pycache__/
# ============================================================

import io
import os
import sys
import zipfile
import base64
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# Enable UTF-8 output on Windows terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stdin.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import config_loader

# ── Constants ────────────────────────────────────────────────
SIZE_LIMIT_MB = 50
EXCLUDE_FILES = {"make_promotion_video.py"}


# ── File collection ──────────────────────────────────────────

def collect_files(robot_num: int, mode_num: int) -> list[Path]:
    """Collect files to submit and return as a list of Paths."""
    files = []

    cfg = ROOT / "config.txt"
    if cfg.exists():
        files.append(cfg)

    robot_dir = ROOT / f"Robot{robot_num}"
    if not robot_dir.exists():
        print(f"[Submit] ERROR: {robot_dir} not found.")
        sys.exit(1)

    for f in sorted(robot_dir.glob("*.py")):
        if f.name not in EXCLUDE_FILES:
            files.append(f)

    rba_dir = robot_dir / "rule_based_algorithms"
    if rba_dir.exists():
        files.extend(sorted(rba_dir.glob("*.py")))

    if mode_num == 2:
        csv = robot_dir / "table_input.csv"
        if csv.exists():
            files.append(csv)

    if mode_num == 4:
        pth = robot_dir / "models" / "model.pth"
        if pth.exists():
            files.append(pth)
        else:
            print(f"[Submit] WARNING: models/model.pth not found (AI mode, skipping).")

    return files


# ── Display ──────────────────────────────────────────────────

def print_header(name: str, comp_name: str) -> None:
    print()
    print("-" * 52)
    print("  aira Algorithm Submission")
    print(f"  Player : {name}")
    print(f"  Race   : {comp_name}")
    print("-" * 52)


def print_file_list(files: list[Path]) -> float:
    print("\nFiles to submit:")
    total = 0.0
    for f in files:
        size_kb = f.stat().st_size / 1024
        rel = str(f.relative_to(ROOT))
        print(f"  - {rel:<47}  ({size_kb:.1f} KB)")
        total += f.stat().st_size
    total_mb = total / (1024 * 1024)
    print(f"\nTotal size: {total_mb:.1f} MB")
    return total_mb


def select_robot(active_robots: list[int]) -> int:
    """If multiple robots are active, ask which one to submit."""
    if len(active_robots) == 1:
        return active_robots[0]
    print(f"\nActive robots: {active_robots}")
    while True:
        ans = input(f"Which robot to submit? ({'/'.join(str(r) for r in active_robots)}): ").strip()
        try:
            num = int(ans)
            if num in active_robots:
                return num
        except ValueError:
            pass
        print(f"  Please enter one of: {active_robots}")


# ── ZIP ──────────────────────────────────────────────────────

def create_zip(files: list[Path]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(f, f.relative_to(ROOT))
    return buf.getvalue()


# ── GAS POST ─────────────────────────────────────────────────

def post_to_gas(gas_url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        gas_url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_comp_type(gas_url: str, comp_name: str) -> str:
    """Return competition type string from GAS, or empty string on error."""
    return config_loader.get_comp_type(gas_url, comp_name)


# ── Main ─────────────────────────────────────────────────────

def main():
    name          = config_loader.NAME
    comp_name     = config_loader.COMPETITION_NAME
    player_token  = config_loader.PLAYER_TOKEN
    gas_url       = config_loader.GAS_SUBMIT_URL
    active_robots = config_loader.ACTIVE_ROBOTS

    print_header(name, comp_name)

    # Pre-flight checks
    if comp_name in ("", "Tutorial"):
        print("[Submit] Tutorial mode: algorithm submission not required.")
        sys.exit(0)

    if not player_token:
        print("\n[Submit] ERROR: PLAYER_TOKEN not found.")
        print("         Open the launcher, set Race Flag to SUBMIT, and save your token.")
        input("\nPress Enter to close...")
        sys.exit(1)

    if not gas_url:
        print("\n[Submit] ERROR: GAS_SUBMIT_URL not found in player_secret.txt.")
        print("         Re-open the launcher and save your token again.")
        input("\nPress Enter to close...")
        sys.exit(1)

    # Competition type check
    comp_type = get_comp_type(gas_url, comp_name)
    if comp_type and comp_type != "Race":
        print(f"[Submit] {comp_type} competition: algorithm submission not required.")
        sys.exit(0)

    # Robot selection
    robot_num = select_robot(active_robots)
    mode_num  = config_loader.get_robot_config(robot_num)["MODE_NUM"]

    # Collect and display files
    files    = collect_files(robot_num, mode_num)
    total_mb = print_file_list(files)

    # Size check
    if total_mb > SIZE_LIMIT_MB:
        print(f"\n[!] Submission is {total_mb:.1f} MB (limit: {SIZE_LIMIT_MB} MB).")
        print()
        print("For large models, please submit manually:")
        print("  1. Upload your files to Google Drive and get a shareable link.")
        print("  2. Email the link to: submit@aira-race.com")
        print(f"     Subject: [Submit] {comp_name} / {name}")
        input("\nPress Enter to close...")
        sys.exit(0)

    # Confirm
    print()
    answer = input("Submit? [Y/n]: ").strip().lower()
    if answer not in ("", "y", "yes"):
        print("\nCancelled. You can submit later by running:")
        print("  python scripts/submit_algorithm.py")
        input("\nPress Enter to close...")
        sys.exit(0)

    # ZIP
    print("\nCompressing files...")
    zip_bytes = create_zip(files)
    print(f"ZIP size: {len(zip_bytes) / (1024 * 1024):.1f} MB")

    # Upload
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{name}_{comp_name}_{timestamp}.zip"
    print(f"Uploading: {file_name} ...")

    payload = {
        "type":         "submit_algorithm",
        "name":         name,
        "comp_name":    comp_name,
        "player_token": player_token,
        "file_name":    file_name,
        "file_data":    base64.b64encode(zip_bytes).decode("utf-8"),
    }

    try:
        result = post_to_gas(gas_url, payload)
    except urllib.error.URLError as e:
        print(f"\n[Submit] ERROR: Upload failed - {e}")
        input("\nPress Enter to close...")
        sys.exit(1)

    if result.get("status") == "success":
        print(f"\nSubmission complete: {result.get('message', '')}")
    else:
        print(f"\n[Submit] ERROR: {result.get('message', 'Unknown error')}")
        input("\nPress Enter to close...")
        sys.exit(1)

    input("\nPress Enter to close...")


if __name__ == "__main__":
    main()
