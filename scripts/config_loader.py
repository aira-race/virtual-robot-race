# config_loader.py
# ============================================================
# Configuration Loader for Virtual Robot Race - Beta 1.7
# ============================================================
# PURPOSE: Reads all settings from a single config.txt at the project root.
#
# ARCHITECTURE:
#   Beta 1.7 unifies global and per-robot settings into one config.txt.
#   Robot IDs (R1, R2, ...) are derived from ACTIVE_ROBOTS automatically.
#   Per-robot MODE_NUM is specified with a prefix: R1_MODE_NUM, R2_MODE_NUM.
#
# USAGE:
#   import config_loader
#   config_loader.HOST          → "localhost"
#   config_loader.ACTIVE_ROBOTS → [1, 2]
#   config_loader.get_robot_config(1) → dict with robot-specific settings
# ============================================================

import os
import re
from pathlib import Path

CONFIG_PATH = "config.txt"

# Default values for all settings in config.txt
DEFAULT_CONFIG = {
    # Player
    "NAME":         "Player0000",   # Player name (alphanumeric, up to 16 chars)
    "COMP_NAME":    "RACE_XXXX",    # Competition name (validated by Unity via GAS)
    # Network
    "HOST":         "localhost",
    "PORT":         12346,
    # System
    "ACTIVE_ROBOTS": "1",           # Comma-separated active robot numbers
    "HEADLESS":     0,              # 0=GUI/CLI launcher, 1=immediate start
    "DEBUG_MODE":   0,              # 0=auto-launch Unity, 1=manual launch
    # Data & Race
    "DATA_SAVE":    1,              # 1=save images/CSV/video, 0=skip
    "RACE_FLAG":    0,              # 1=submit to leaderboard, 0=test only
    "X_POST_FLAG":  0,              # 1=post to X on finish, 0=skip
    # Robot modes (per-robot, prefix R1_ / R2_)
    "R1_MODE_NUM":  1,              # 1=keyboard,2=table,3=rule_based,4=ai,5=smartphone
    "R2_MODE_NUM":  1,
}

# Keys that should be parsed as integers
INT_KEYS = {
    "PORT",
    "HEADLESS",
    "DEBUG_MODE",
    "DATA_SAVE",
    "RACE_FLAG",
    "X_POST_FLAG",
    "R1_MODE_NUM",
    "R2_MODE_NUM",
}

# Global config storage (populated by apply_config())
CONFIG = DEFAULT_CONFIG.copy()

# Robot configs cache (indexed by robot number: 1, 2, ...)
ROBOT_CONFIGS = {}


def _strip_inline_comment(value: str) -> str:
    """Remove inline comments starting with '#'. 'Andy00  # comment' -> 'Andy00'"""
    return value.split('#', 1)[0].strip()


def _strip_quotes(value: str) -> str:
    """Remove surrounding single or double quotes. '"Andy00"' -> 'Andy00'"""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def load_config() -> None:
    """Load all settings from config.txt into CONFIG dict."""
    if not os.path.exists(CONFIG_PATH):
        print(f"[Config] {CONFIG_PATH} not found. Using defaults.")
        return

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = _strip_quotes(_strip_inline_comment(value.strip()))

                if key in DEFAULT_CONFIG:
                    if key in INT_KEYS:
                        try:
                            CONFIG[key] = int(value)
                        except ValueError:
                            print(f"[Config] WARNING: Invalid integer for {key}='{value}'. Using default.")
                            CONFIG[key] = DEFAULT_CONFIG[key]
                    else:
                        CONFIG[key] = value
                # Unknown keys are silently ignored (forward compatibility)

    except Exception as e:
        print(f"[Config] Failed to read {CONFIG_PATH}: {e}")


def validate_name(name: str) -> str:
    """
    Validate NAME: alphanumeric and underscore, 1-16 characters.
    Returns the name if valid, or the default if not.
    """
    if re.fullmatch(r"[A-Za-z0-9_]{1,16}", name or ""):
        return name
    print(f"[Config] WARNING: Invalid NAME='{name}'. Must be 1-16 alphanumeric characters or underscores. Using default.")
    return DEFAULT_CONFIG["NAME"]


def _build_robot_config(robot_num: int) -> dict:
    """
    Build a per-robot config dict from the unified config.txt.
    ROBOT_ID is derived from robot_num (1 -> "R1", 2 -> "R2", ...).
    MODE_NUM is read from R{N}_MODE_NUM in the global config.
    Other settings (NAME, DATA_SAVE, RACE_FLAG, etc.) are shared globals.
    """
    robot_id = f"R{robot_num}"
    mode_key = f"R{robot_num}_MODE_NUM"
    mode_num = CONFIG.get(mode_key, DEFAULT_CONFIG.get("R1_MODE_NUM", 1))

    data_save = CONFIG.get("DATA_SAVE", 1)

    robot_config = {
        "ROBOT_ID":     robot_id,
        "NAME":         validate_name(CONFIG.get("NAME", DEFAULT_CONFIG["NAME"])),
        "COMP_NAME":    CONFIG.get("COMP_NAME", DEFAULT_CONFIG["COMP_NAME"]),
        "MODE_NUM":     mode_num,
        "DATA_SAVE":    data_save,
        "RACE_FLAG":    CONFIG.get("RACE_FLAG", 0),
        "X_POST_FLAG":  CONFIG.get("X_POST_FLAG", 0),
        # Video settings derived from DATA_SAVE (advanced users can adjust constants here)
        "AUTO_MAKE_VIDEO": 1 if data_save == 1 else 0,
        "VIDEO_FPS":    20,
        "INFER_FPS":    1,
    }

    print(f"[Config] Robot{robot_num}: id={robot_id}, mode={get_mode_string(mode_num)}, "
          f"data_save={data_save}, race_flag={robot_config['RACE_FLAG']}")
    return robot_config


def apply_config() -> None:
    """
    Load config.txt and expose settings as module-level variables.
    Also pre-builds robot configs for all active robots.
    Called automatically at import time.
    """
    global HOST, PORT, ACTIVE_ROBOTS, HEADLESS, DEBUG_MODE
    global NAME, COMP_NAME, DATA_SAVE, RACE_FLAG, X_POST_FLAG

    load_config()

    HOST        = CONFIG["HOST"]
    PORT        = CONFIG["PORT"]
    HEADLESS    = CONFIG["HEADLESS"]
    DEBUG_MODE  = CONFIG["DEBUG_MODE"]
    NAME        = validate_name(CONFIG["NAME"])
    COMP_NAME   = CONFIG["COMP_NAME"]
    DATA_SAVE   = CONFIG["DATA_SAVE"]
    RACE_FLAG   = CONFIG["RACE_FLAG"]
    X_POST_FLAG = CONFIG["X_POST_FLAG"]

    # Parse comma-separated robot numbers into a list of ints: "1,2" -> [1, 2]
    ACTIVE_ROBOTS = [int(r.strip()) for r in CONFIG.get("ACTIVE_ROBOTS", "1").split(",")]

    # Pre-build robot configs for all active robots
    for robot_num in ACTIVE_ROBOTS:
        ROBOT_CONFIGS[robot_num] = _build_robot_config(robot_num)


def get_robot_config(robot_num: int) -> dict:
    """
    Get config dict for a specific robot number.
    Builds on demand if not already cached.
    """
    if robot_num not in ROBOT_CONFIGS:
        ROBOT_CONFIGS[robot_num] = _build_robot_config(robot_num)
    return ROBOT_CONFIGS[robot_num]


def get_mode_string(mode_num: int) -> str:
    """Convert MODE_NUM integer to mode name string."""
    MODE_MAP = {
        1: "keyboard",
        2: "table",
        3: "rule_based",
        4: "ai",
        5: "smartphone",
        6: "rl_training",
    }
    return MODE_MAP.get(mode_num, "keyboard")


# Initialize at import time
apply_config()
