# VRR Beta 1.3: Rule-Based Control System - Detailed Code Walkthrough

This document provides a line-by-line explanation of the rule-based control system (MODE_NUM=3) in the Virtual Robot Race project. It is designed for audio explanation via NotebookLM.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [rule_based_input.py - Main Control Loop](#2-rule_based_inputpy---main-control-loop)
3. [driver_model.py - Driving Decision Engine](#3-driver_modelpy---driving-decision-engine)
4. [sliding_windows.py - Lane Detection](#4-sliding_windowspy---lane-detection)
5. [perception_Startsignal.py - Start Signal Detection](#5-perception_startsignalpy---start-signal-detection)
6. [perception_Lane.py - Red Lane Detection](#6-perception_lanepy---red-lane-detection)
7. [status_Robot.py - Robot State Machine](#7-status_robotpy---robot-state-machine)
8. [debug_utils.py - Debug Visualization](#8-debug_utilspy---debug-visualization)
9. [Linetrace_white.py - Legacy PID Control](#9-linetrace_whitepy---legacy-pid-control)
10. [Data Flow Summary](#10-data-flow-summary)

---

## 1. System Overview

The rule-based control system consists of these core components:

```
Camera Image (RGB)
       |
       v
+------------------+
| Start Signal     |  <-- perception_Startsignal.py
| Detection        |
+------------------+
       |
       v (GO signal)
+------------------+
| Lane Detection   |  <-- sliding_windows.py
| (Sliding Window) |
+------------------+
       |
       v (lateral_px, theta_deg)
+------------------+
| Driver Model     |  <-- driver_model.py
| (Control Logic)  |
+------------------+
       |
       v (driveTorque, steerAngle)
+------------------+
| Unity Robot      |
+------------------+
```

The main loop runs at approximately 20Hz, processing each camera frame to determine steering and throttle commands.

---

## 2. rule_based_input.py - Main Control Loop

This is the entry point for rule-based control. It coordinates all perception and control modules.

### Lines 1-11: File Header and Imports

```python
# rule_based_input.py (Robot1 version - New Architecture)
# Rule-based driving using sliding window lane detection and driver model
# Compatible with Unity Server + Python Client architecture

import time
import os
import sys
import importlib.util
from pathlib import Path
from PIL import Image
```

**Explanation:**
- Lines 1-3: Comments describing the file purpose. This file implements rule-based autonomous driving.
- Line 5: `time` module - used for timing operations (though not heavily used in current code).
- Line 6: `os` module - provides operating system interface for file paths.
- Line 7: `sys` module - used to modify Python's module search path.
- Line 8: `importlib.util` - advanced import mechanism to load modules dynamically without cache conflicts.
- Line 9: `Path` from pathlib - object-oriented filesystem path handling.
- Line 10: `Image` from PIL - Python Imaging Library for loading camera images.

### Lines 12-20: Module Path Setup

```python
# Module identification
MODULE_SOURCE = "Robot1"
print(f"[rule_based_input] Loaded from {MODULE_SOURCE}/")

# Import data_manager functions for Robot1
_this_dir = Path(__file__).parent
sys.path.insert(0, str(_this_dir.parent))  # Add Project_Beta to path
sys.path.insert(0, str(_this_dir))  # Add Robot1 to path (for rule_based_algorithms)
import data_manager
```

**Explanation:**
- Line 13: `MODULE_SOURCE = "Robot1"` - identifies this code belongs to Robot1 (vs Robot2).
- Line 14: Prints a startup message showing which robot's code is loaded.
- Line 17: `Path(__file__).parent` - gets the directory containing this script (Robot1 folder).
- Line 18: `sys.path.insert(0, ...)` - adds Project_Beta folder to Python's module search path at highest priority.
- Line 19: Adds Robot1 folder to the path so `rule_based_algorithms` can be imported.
- Line 20: `import data_manager` - imports the shared data manager that provides camera images and sensor data.

### Lines 22-40: Algorithm Imports

```python
# Import rule-based algorithms
from rule_based_algorithms import status_Robot
from rule_based_algorithms.sliding_windows import sliding_windows_white
from rule_based_algorithms.driver_model import DriverModel, DriverConfig

# Load perception_Startsignal using importlib to avoid module cache conflicts
_startsignal_path = _this_dir / "rule_based_algorithms" / "perception_Startsignal.py"
_startsignal_spec = importlib.util.spec_from_file_location(
    f"perception_Startsignal_{MODULE_SOURCE}",  # Unique module name per robot
    _startsignal_path
)
_startsignal_module = importlib.util.module_from_spec(_startsignal_spec)
_startsignal_spec.loader.exec_module(_startsignal_module)
detect_start_signal = _startsignal_module.detect_start_signal

# Debug utilities
from rule_based_algorithms.debug_utils import annotate_and_save_canvas
from rule_based_algorithms.debug_utils import overlay_and_save as overlay_and_save_fallback
```

**Explanation:**
- Line 23: Imports `status_Robot` - simple state machine for robot status.
- Line 24: Imports `sliding_windows_white` - the main lane detection algorithm.
- Line 25: Imports `DriverModel` and `DriverConfig` - the control decision engine.
- Lines 28-35: **Dynamic module loading** - This is a critical technique:
  - Line 28: Builds the full path to perception_Startsignal.py.
  - Lines 29-32: Creates a "module spec" with a unique name (`perception_Startsignal_Robot1`).
  - Line 33: Creates an actual module object from the spec.
  - Line 34: Executes the module code to initialize it.
  - Line 35: Extracts just the `detect_start_signal` function.
  - **Why?** Robot1 and Robot2 may have different calibration. Using `importlib.util` prevents Python from caching one robot's module and accidentally using it for both.
- Lines 38-39: Import debug utilities for saving annotated images.

### Lines 41-61: Global Variables and Configuration

```python
# --- Globals (control output) ---
robot_id = "R1"
driveTorque: float = 0.0
steerAngle: float = 0.0

# --- Internal state ---
_started_latch = False  # Once GO is detected, stays True
SAVE_DEBUG_OVERLAYS = True  # Save overlay images to debug/ every frame

# Lane-loss handling
_lost_age = 0
HOLD_SEC = 2.0
PERIOD = 0.050
HOLD_FRAMES = max(1, int(HOLD_SEC / PERIOD))

# Mode labels for logging readability
MODE_LABELS = {
    "normal": "Normal",
    "hold": "Hold",
    "search": "Search",
}
```

**Explanation:**
- Line 43: `robot_id = "R1"` - identifier string sent to Unity server.
- Lines 44-45: `driveTorque` and `steerAngle` - the output control commands (floats between -1.0 and 1.0).
- Line 48: `_started_latch = False` - a "latch" that remembers if the start signal has been detected. Once True, it stays True.
- Line 49: `SAVE_DEBUG_OVERLAYS = True` - when True, saves annotated images every frame for debugging.
- Line 52: `_lost_age = 0` - counter tracking how many consecutive frames the lane has been lost.
- Line 53: `HOLD_SEC = 2.0` - when lane is lost, hold previous steering for 2 seconds.
- Line 54: `PERIOD = 0.050` - expected loop period (50ms = 20Hz).
- Line 55: `HOLD_FRAMES = max(1, int(HOLD_SEC / PERIOD))` - converts 2 seconds to frame count (40 frames).
- Lines 57-61: `MODE_LABELS` dictionary - maps internal mode names to display-friendly labels.

### Lines 63-78: Driver Model Initialization

```python
# Driver (final decision maker for steer-type control)
_driver = DriverModel(DriverConfig(
    image_width=224,
    forward_sign=+1,
    v_min=0.15,
    v_max=0.75,
    k_theta=0.90,
    k_lateral=0.60,
    steer_limit=0.785,  # ~45 degrees max
    alpha_smooth=0.30,
    torque_limit=1.00,
    theta_hard_limit_deg=80.0,
    use_soc_scaling=True,
    soc_floor=0.30,
))
```

**Explanation:**
- Line 64: Creates a `DriverModel` instance with configuration.
- Line 65: `image_width=224` - expected image width in pixels for normalization.
- Line 66: `forward_sign=+1` - positive torque means forward motion.
- Line 67: `v_min=0.15` - minimum speed (15% throttle) to prevent stalling.
- Line 68: `v_max=0.75` - maximum speed (75% throttle) for stability.
- Line 69: `k_theta=0.90` - gain for heading angle correction (higher = stronger response).
- Line 70: `k_lateral=0.60` - gain for lateral position correction.
- Line 71: `steer_limit=0.785` - maximum steering angle in radians (~45 degrees).
- Line 72: `alpha_smooth=0.30` - smoothing factor for output (0.3 means 30% old value + 70% new value).
- Line 73: `torque_limit=1.00` - maximum allowed torque (100%).
- Line 74: `theta_hard_limit_deg=80.0` - if heading exceeds 80 degrees, treat as invalid detection.
- Line 75: `use_soc_scaling=True` - scale speed based on battery state-of-charge.
- Line 76: `soc_floor=0.30` - minimum speed multiplier at low battery (30%).

### Lines 80-93: Helper Functions

```python
def saturate(value, min_val=-1.0, max_val=1.0):
    """Clamp value within [min_val, max_val]."""
    return max(min_val, min(max_val, value))


def get_latest_command():
    """Return latest control command for WebSocket sender."""
    return {
        "type": "control",
        "robot_id": robot_id,
        "driveTorque": round(float(driveTorque), 3),
        "steerAngle": round(float(steerAngle), 3),
    }
```

**Explanation:**
- Lines 80-82: `saturate()` - classic clamp function. Ensures value stays within bounds.
  - `max(min_val, min(max_val, value))` - first caps at max_val, then raises to min_val if too low.
- Lines 85-92: `get_latest_command()` - packages control values into a dictionary for network transmission.
  - Line 87: `"type": "control"` - message type identifier.
  - Line 88: `"robot_id": robot_id` - which robot this command is for ("R1").
  - Lines 89-90: The actual control values, rounded to 3 decimal places for cleaner transmission.

### Lines 95-146: The Main Update Function (Part 1 - Input Processing)

```python
def update():
    """
    Single update cycle for rule-based control.
    Called repeatedly by main.py at ~20Hz.
    Returns True if successful, False if should stop.
    """
    global driveTorque, steerAngle, _started_latch, _lost_age

    try:
        # === Inputs ===
        soc = data_manager.get_latest_soc(robot_id)  # float 0.0..1.0 (can be None)
        rgb_path = data_manager.get_latest_rgb_path(robot_id)

        if not rgb_path or not rgb_path.exists():
            # No image available yet
            return True

        try:
            pil_img = Image.open(rgb_path).convert("RGB")
        except Exception:
            return True

        # === Start signal (latched) ===
        if not _started_latch:
            raw_go = detect_start_signal(pil_img)
            if raw_go:
                _started_latch = True
                status_Robot.set_state(status_Robot.RUN_STRAIGHT)
                print(f"[{robot_id} RuleBased] START latched")

        start_go = _started_latch  # official GO/NO-GO passed to driver
```

**Explanation:**
- Line 95: `def update()` - the main control loop function, called every frame.
- Lines 96-100: Docstring explaining purpose - runs at ~20Hz (50ms cycle).
- Line 101: `global` statement - allows modification of module-level variables.
- Line 104: Wraps everything in try/except for robustness.
- Line 105: `data_manager.get_latest_soc(robot_id)` - retrieves battery State of Charge (0.0 to 1.0).
- Line 106: `data_manager.get_latest_rgb_path(robot_id)` - gets path to latest camera image.
- Lines 108-110: If no image path or file doesn't exist, return True (continue running, just skip this frame).
- Lines 112-115: Try to open the image file. If it fails (e.g., corrupted), skip this frame.
- Lines 118-124: **Start signal detection logic:**
  - Line 118: Only check if we haven't started yet (`not _started_latch`).
  - Line 119: Call the start signal detector on current image.
  - Lines 120-123: If start detected:
    - Set `_started_latch = True` - this is permanent until reset.
    - Update robot state to `RUN_STRAIGHT`.
    - Print confirmation message.
- Line 125: `start_go = _started_latch` - simple alias for clarity.

### Lines 127-147: Lane Perception

```python
        # === Lane perception (only after GO) ===
        if start_go:
            try:
                sw = sliding_windows_white(
                    pil_img, save_debug=False, src_path=str(rgb_path), return_canvas=True
                )
            except TypeError:
                # Backward compatibility: older version without return_canvas
                sw = sliding_windows_white(pil_img, save_debug=False, src_path=str(rgb_path))

            lane_ok = bool(getattr(sw, "ok", False))
            lateral = getattr(sw, "lateral_px", None) if lane_ok else None
            theta = getattr(sw, "theta_deg", None) if lane_ok else None
            img_w = getattr(sw, "img_width", None) or pil_img.size[0]
            single_side = bool(getattr(sw, "single_side", False))
        else:
            lane_ok = False
            lateral, theta = None, None
            img_w = pil_img.size[0]
            sw = None
            single_side = False
```

**Explanation:**
- Line 128: Only do lane detection after the race has started.
- Lines 129-135: Call the sliding windows algorithm:
  - `pil_img` - the camera image.
  - `save_debug=False` - don't save debug images here (done later).
  - `src_path=str(rgb_path)` - original file path for naming.
  - `return_canvas=True` - return the debug visualization canvas.
  - Lines 133-135: Fallback for older versions that don't support `return_canvas`.
- Line 137: `lane_ok = bool(getattr(sw, "ok", False))` - safely get the `ok` attribute, default to False.
- Line 138: If lane detected, get lateral offset in pixels (positive = right of center).
- Line 139: If lane detected, get heading angle in degrees (positive = tilted right).
- Line 140: Get image width, fallback to PIL image size.
- Line 141: Get single_side flag (True if only one lane boundary was detected).
- Lines 142-147: If not started, set all perception values to defaults.

### Lines 149-171: Mode Decision and Driver Update

```python
        # === Determine lane_mode from lane state ===
        if lane_ok:
            _lost_age = 0
            lane_mode = "normal"
        else:
            _lost_age += 1
            lane_mode = "hold" if _lost_age <= HOLD_FRAMES else "search"

        # === Driver update (drive/steer decision) ===
        drive, steer = _driver.update(
            lateral_px=lateral,
            theta_deg=theta,
            soc=soc,
            image_width=img_w,
            start_go=start_go,
            valid_lane=lane_ok,
            lane_mode=lane_mode,
            lost_age=_lost_age,
            single_side=single_side,
        )

        driveTorque = saturate(drive)
        steerAngle = saturate(steer, -0.785, 0.785)  # Limit steer to ~±45 deg
```

**Explanation:**
- Lines 150-156: **Lane mode state machine:**
  - If `lane_ok` is True: reset `_lost_age` to 0, set mode to "normal".
  - If lane is lost: increment `_lost_age` by 1.
    - If lost for <= HOLD_FRAMES (40 frames ≈ 2 seconds): mode = "hold" (keep previous steering).
    - If lost for > HOLD_FRAMES: mode = "search" (actively search for lane).
- Lines 158-169: Call the driver model with all perception data:
  - `lateral_px` - lane center offset in pixels.
  - `theta_deg` - heading angle in degrees.
  - `soc` - battery level.
  - `image_width` - for normalization.
  - `start_go` - whether race has started.
  - `valid_lane` - whether lane was detected.
  - `lane_mode` - "normal", "hold", or "search".
  - `lost_age` - consecutive frames without lane detection.
  - `single_side` - flag for estimated lane.
- Lines 170-171: Saturate outputs to valid ranges:
  - driveTorque: -1.0 to 1.0.
  - steerAngle: -0.785 to 0.785 radians (±45 degrees).

### Lines 173-235: Debug Output and Logging

```python
        # === Debug overlay save (per frame, after GO) ===
        if SAVE_DEBUG_OVERLAYS and start_go:
            try:
                frame_name = data_manager.get_latest_frame_name(robot_id)
                debug_dir = Path(__file__).parent / "debug"

                # Determine display mode (include Pulse state)
                debug_use_pulse = _driver.last_debug.get("use_pulse", False)
                debug_pulse_phase = _driver.last_debug.get("pulse_phase", "")
                if debug_use_pulse:
                    display_mode = f"Pulse({debug_pulse_phase})"
                else:
                    display_mode = MODE_LABELS.get((lane_mode or "").lower(), lane_mode)

                if sw is not None and getattr(sw, "canvas_bgr", None) is not None:
                    # 1) If SW canvas exists, annotate and save
                    outp = annotate_and_save_canvas(
                        sw.canvas_bgr,
                        out_dir=str(debug_dir),
                        lateral_px=lateral,
                        theta_deg=theta,
                        drive_torque=driveTorque,
                        steer_angle=steerAngle,
                        mode=display_mode,
                        frame_name=frame_name,
                        src_path=str(rgb_path),
                        jpeg_quality=85,
                    )
                else:
                    # 2) Fallback: annotate raw frame with numbers only
                    outp = overlay_and_save_fallback(
                        pil_img,
                        sw_result=sw,
                        driver_debug=_driver.last_debug,
                        out_dir=str(debug_dir),
                    )

                if outp and (_lost_age % 20 == 0 or _lost_age == 1):  # Log periodically
                    print(f"[{robot_id} RuleBased] Saved debug: {outp}")
            except Exception as e:
                if _lost_age % 20 == 0:  # Log errors periodically
                    print(f"[{robot_id} RuleBased] Debug overlay save failed: {e}")
```

**Explanation:**
- Line 174: Only save debug images if enabled AND race has started.
- Line 176: Get the frame name (e.g., "frame_000123.jpg") for consistent naming.
- Line 177: Debug images go to Robot1/debug folder.
- Lines 180-185: Build the display mode string:
  - If pulse throttle is active, show "Pulse(ON)" or "Pulse(OFF)".
  - Otherwise show "Normal", "Hold", or "Search".
- Lines 187-200: If sliding window canvas exists, use the preferred method:
  - `annotate_and_save_canvas()` adds HUD overlay to the already-processed image.
- Lines 201-207: Fallback when no canvas available:
  - `overlay_and_save_fallback()` draws HUD on raw image.
- Lines 209-213: Log debug output, but only every 20 frames to avoid console spam.

### Lines 216-240: Periodic Logging and Error Handling

```python
        # === Logging (every 20 frames = ~1 second) ===
        if _lost_age % 20 == 0 or not start_go:
            mode_label = MODE_LABELS.get((lane_mode or "").lower(), str(lane_mode))
            # Check if pulse mode is active
            use_pulse = _driver.last_debug.get("use_pulse", False)
            pulse_phase = _driver.last_debug.get("pulse_phase", "")
            if use_pulse:
                mode_label = f"Pulse({pulse_phase})"
            lat_str = "None" if (lateral is None) else f"{lateral:+.1f}"
            tht_str = "None" if (theta is None) else f"{theta:+.1f}"
            soc_str = "None" if (soc is None) else f"{float(soc):.2f}"
            import math
            steer_deg = math.degrees(steerAngle)

            print(
                f"[{robot_id} RuleBased] Drive={driveTorque:+.2f} Steer={steerAngle:+.3f}rad({steer_deg:+.1f}°) | "
                f"GO={start_go} LaneOK={lane_ok}, {mode_label} LostAge={_lost_age} "
                f"Lat={lat_str} Theta={tht_str} SOC={soc_str}"
            )

        return True

    except Exception as e:
        print(f"[{robot_id} RuleBased] Error: {e}")
        return True
```

**Explanation:**
- Line 217: Log every 20 frames (~1 second at 20Hz) or when waiting for start.
- Lines 218-223: Build human-readable mode label.
- Lines 224-226: Format numeric values with "None" fallback.
- Lines 227-228: Convert steer angle from radians to degrees for readability.
- Lines 230-234: Print comprehensive status line:
  - Drive and steer values.
  - GO status, lane detection status, mode.
  - Lost age counter, lateral/theta values, battery SOC.
- Line 236: Return True to indicate "keep running".
- Lines 238-240: Catch any exceptions, log them, but keep running.

### Lines 243-251: Reset Function

```python
def reset():
    """Reset rule-based control state."""
    global _started_latch, _lost_age, driveTorque, steerAngle
    _started_latch = False
    _lost_age = 0
    driveTorque = 0.0
    steerAngle = 0.0
    print(f"[{robot_id} RuleBased] State reset")
```

**Explanation:**
- Line 243: `def reset()` - called when resetting for a new race.
- Line 245: Declare globals to modify.
- Line 246: Reset the start latch - robot will wait for start signal again.
- Line 247: Reset lost age counter.
- Lines 248-249: Zero out control outputs.
- Line 250: Print confirmation.

---

## 3. driver_model.py - Driving Decision Engine

This module computes the actual drive and steer commands based on perception data.

### Lines 1-18: File Header and Helper Function

```python
# rule_based_algorithms/driver_model.py
# ----------------------------------------------------------------------
# STEER-TYPE CONTROL VERSION
# Higher layer decides lane_mode ("normal" / "hold" / "search") and lost_age.
# This driver computes: (drive_torque, steer_angle) for steer-type robots.
#
# Sign conventions:
#   lateral_px : right is + [px] (offset from image center)
#   theta_deg  : 0° is up, tilting to the right is + [deg]
#   Output:
#     drive_torque : forward torque (-1.0 to +1.0, + is forward)
#     steer_angle  : steering angle in radians (+ is right turn)
# ----------------------------------------------------------------------

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple, Dict
import math

def _clip(x: float, lo: float, hi: float) -> float:
    """Clamp x into [lo, hi]."""
    return lo if x < lo else hi if x > hi else x
```

**Explanation:**
- Lines 1-12: Detailed header documenting sign conventions. This is critical for understanding the math:
  - `lateral_px`: positive = robot is to the RIGHT of lane center.
  - `theta_deg`: 0° = straight ahead, positive = tilted RIGHT.
  - `drive_torque`: positive = forward motion.
  - `steer_angle`: positive = turn RIGHT.
- Lines 15-17: Standard imports.
- Lines 20-22: `_clip()` function - more compact version of saturate. Uses ternary operators.

### Lines 25-72: DriverConfig Dataclass

```python
@dataclass
class DriverConfig:
    # Geometry / normalization
    image_width: int = 224
    lateral_norm_halfwidth_px: Optional[float] = None  # None → image_width/2

    # Speed planning (auto slow-down in curves)
    v_min: float = 0.15             # Reduced for better curve handling
    v_max: float = 0.55             # Reduced for stability (was 0.70)
    slow_w_theta: float = 0.70
    slow_w_lateral: float = 0.60

    # Steering blend (Yaw: right is +)
    k_theta: float = 0.45          # Gain for theta (was 0.90)
    k_lateral: float = 0.30        # Gain for lateral offset (was 0.60)
    steer_limit: float = 0.785     # Max steer angle (radians, ~45 deg)

    # Output shaping
    torque_limit: float = 1.00
    alpha_smooth: float = 0.50     # Increased smoothing to reduce oscillation

    # Battery (SOC) scaling
    use_soc_scaling: bool = True
    soc_floor: float = 0.30

    # Conventions / safety
    forward_sign: int = +1
    theta_hard_limit_deg: float = 80.0
    invalid_brake: float = 0.0        # output when NO-GO
    require_start_go: bool = True     # True: must stop if NO-GO

    # ====== Lane-lost related ======
    hold_decay_per_frame: float = 0.90   # decay ratio during hold
    search_pivot: bool = True            # True: pivot in place
    search_speed: float = 0.00           # forward component (0.0 when pivoting)
    search_steer_const: float = 0.6      # constant steer angle during search (~34 deg)
    loop_period_s: float = 0.050         # for logs only

    # ====== Pulse control for curves (ちょんちょんアクセル) ======
    pulse_enabled: bool = True           # Enable pulse throttle in curves
    pulse_theta_threshold: float = 25.0  # Start pulsing when |theta| > this [deg]
    pulse_lateral_threshold: float = 30.0  # Or when |lateral| > this [px]
    pulse_on_frames: int = 3             # Frames with throttle ON
    pulse_off_frames: int = 3            # Frames with throttle OFF (coast)
    pulse_drive_on: float = 0.35         # Throttle value during ON phase
    pulse_drive_off: float = 0.0         # Throttle value during OFF phase
```

**Explanation:**
- Line 25: `@dataclass` decorator - automatically generates `__init__`, `__repr__`, etc.
- Line 27-28: Geometry parameters for normalization.
- Lines 31-34: Speed control:
  - `v_min = 0.15` - minimum 15% throttle to prevent stalling.
  - `v_max = 0.55` - reduced from 0.70 for stability.
  - `slow_w_theta` and `slow_w_lateral` - weights for speed reduction (currently unused in favor of simpler formula).
- Lines 37-39: Steering gains:
  - `k_theta = 0.45` - how strongly to correct for heading error.
  - `k_lateral = 0.30` - how strongly to correct for position error.
  - `steer_limit = 0.785` - maximum steering (45 degrees in radians).
- Lines 42-43: Output smoothing:
  - `alpha_smooth = 0.50` - IIR filter coefficient. Higher = smoother but slower response.
- Lines 46-47: Battery-based speed scaling:
  - `soc_floor = 0.30` - even at 0% battery, speed multiplier is at least 0.3.
- Lines 50-53: Safety parameters.
- Lines 56-60: Lane-lost behavior:
  - `hold_decay_per_frame = 0.90` - each frame in hold mode, multiply speed/steer by 0.9.
  - `search_pivot = True` - when searching, rotate in place (don't move forward).
  - `search_steer_const = 0.6` - constant ~34 degree turn during search.
- Lines 63-70: **Pulse control ("ちょんちょんアクセル" = tap-tap throttle):**
  - A technique for curves: alternate between throttle ON and OFF.
  - `pulse_theta_threshold = 25.0` - activate when heading error > 25 degrees.
  - `pulse_on_frames = 3` - throttle on for 3 frames.
  - `pulse_off_frames = 3` - coast for 3 frames.
  - `pulse_drive_on = 0.35` - 35% throttle during ON phase.

### Lines 74-93: DriverModel Class Initialization

```python
class DriverModel:
    """Given lane_mode, produce (drive_torque, steer_angle) for steer-type control."""

    def __init__(self, cfg: DriverConfig):
        self.cfg = cfg
        self._prev_drive = 0.0
        self._prev_steer = 0.0
        self._half_w = max(
            1.0,
            (cfg.lateral_norm_halfwidth_px
             if cfg.lateral_norm_halfwidth_px is not None
             else cfg.image_width * 0.5)
        )
        # For hold mode, remember most recent base/steer
        self._last_base = 0.0
        self._last_steer = 0.0
        # Pulse control state
        self._pulse_counter = 0  # Frame counter for pulse timing
        self._pulse_phase = True  # True = ON phase, False = OFF phase
        self.last_debug: Dict[str, float | int | str | bool | None] = {}
```

**Explanation:**
- Line 77: Store configuration.
- Lines 78-79: Previous output values for smoothing filter.
- Lines 80-85: Calculate half-width for normalization:
  - If `lateral_norm_halfwidth_px` is specified, use it.
  - Otherwise, use half of image_width.
  - `max(1.0, ...)` prevents division by zero.
- Lines 87-88: Store last good values for hold mode.
- Lines 90-91: Pulse control state machine variables.
- Line 92: Debug dictionary to expose internal state.

### Lines 95-118: Update Method - Entry and Safety Checks

```python
    def update(
        self,
        lateral_px: Optional[float],
        theta_deg: Optional[float],
        soc: Optional[float],
        image_width: Optional[int],
        start_go: bool,
        valid_lane: bool,
        lane_mode: str = "normal",
        lost_age: int = 0,
        single_side: bool = False,
    ) -> Tuple[float, float]:
        """Compute (drive_torque, steer_angle) for the current frame."""
        # Geometry update
        if image_width is not None and image_width > 0:
            self._half_w = max(1.0, image_width * 0.5)

        # Start gate
        if self.cfg.require_start_go and not start_go:
            drive = steer = self.cfg.invalid_brake * self.cfg.forward_sign
            drive, steer = self._smooth(drive, steer)
            self._store_debug(False, False, lane_mode, lateral_px, theta_deg,
                              0.0, 0.0, 0.0, drive, steer, soc, None, None, lost_age)
            return drive, steer
```

**Explanation:**
- Lines 95-106: Method signature with all inputs:
  - `lateral_px` - lane center offset.
  - `theta_deg` - heading angle.
  - `soc` - battery level.
  - `image_width` - for normalization.
  - `start_go` - has race started.
  - `valid_lane` - is lane detected.
  - `lane_mode` - "normal"/"hold"/"search".
  - `lost_age` - frames since lane was last seen.
  - `single_side` - was lane estimated from one side only.
- Lines 109-110: Update half-width if image size changed.
- Lines 113-118: **Start gate check:**
  - If `require_start_go` is True and race hasn't started, output zero (brake).
  - Apply smoothing even to zero output for gradual stop.
  - Store debug info and return.

### Lines 120-130: SOC Scaling

```python
        # Angle sanity: if theta is absurd, treat as invalid detection
        if theta_deg is not None and abs(float(theta_deg)) > self.cfg.theta_hard_limit_deg:
            valid_lane = False

        # SOC scaling
        scale = 1.0
        if self.cfg.use_soc_scaling and (soc is not None):
            s = _clip(float(soc), 0.0, 1.0)
            scale = _clip(self.cfg.soc_floor + (1.0 - self.cfg.soc_floor) * s,
                          self.cfg.soc_floor, 1.0)

        mode = (lane_mode or "normal").lower()
```

**Explanation:**
- Lines 121-122: **Angle sanity check:**
  - If `theta_deg` exceeds 80 degrees, it's probably a misdetection.
  - Set `valid_lane = False` to trigger hold/search behavior.
- Lines 125-129: **SOC scaling formula:**
  - `scale = soc_floor + (1 - soc_floor) * soc`
  - At soc=1.0 (full battery): scale = 0.30 + 0.70 * 1.0 = 1.0.
  - At soc=0.5 (half battery): scale = 0.30 + 0.70 * 0.5 = 0.65.
  - At soc=0.0 (empty battery): scale = 0.30 + 0.70 * 0.0 = 0.30.
  - This prevents complete stop at low battery while still reducing speed.
- Line 131: Normalize mode string to lowercase.

### Lines 133-195: Normal Mode - Core Control Logic

```python
        # ---------------- normal ----------------
        if mode == "normal":
            if not (valid_lane and (lateral_px is not None) and (theta_deg is not None)):
                mode = "hold"
            else:
                lateral_n = float(lateral_px) / self._half_w
                theta_rad = math.radians(float(theta_deg))

                # Calculate steer angle directly
                steer = self.cfg.k_theta * theta_rad + self.cfg.k_lateral * lateral_n
                steer = _clip(steer, -self.cfg.steer_limit, self.cfg.steer_limit)

                # Slow down in curves based on steer angle
                steer_cost = abs(steer) / self.cfg.steer_limit
                base = self.cfg.v_max * max(0.0, 1.0 - steer_cost * 0.7)
                base = max(self.cfg.v_min, min(self.cfg.v_max, base))

                # Ensure a minimum base speed when cornering hard
                corner_base_floor = 0.28
                theta_thr_deg = 15.0
                if abs(theta_deg) >= theta_thr_deg:
                    base = max(base, corner_base_floor)

                self._last_base = base
                self._last_steer = steer
```

**Explanation:**
- Line 134: Enter normal mode processing.
- Lines 135-136: If lane data is invalid, fall through to hold mode.
- Line 138: `lateral_n` - normalize lateral offset to range roughly -1 to +1.
  - At `lateral_px = half_w` (edge of image), `lateral_n = 1.0`.
- Line 139: Convert `theta_deg` to radians for calculation.
- Lines 142-143: **Steering calculation:**
  - `steer = k_theta * theta_rad + k_lateral * lateral_n`
  - This is a proportional controller combining two error sources.
  - Clip to maximum steering limit.
- Lines 146-148: **Speed planning:**
  - `steer_cost` = how hard are we steering (0 to 1).
  - `base = v_max * (1 - steer_cost * 0.7)` - reduce speed when steering hard.
  - Example: At full steering, base = 0.55 * (1 - 0.7) = 0.165.
- Lines 151-154: **Corner speed floor:**
  - When heading error > 15 degrees, ensure at least 28% speed.
  - This prevents stalling in tight corners.
- Lines 156-157: Store values for hold mode recovery.

### Lines 159-195: Pulse Control (Tap-Tap Throttle)

```python
                # ====== Pulse control for curves (ちょんちょんアクセル) ======
                # Disable pulse when single_side (estimated lane is less accurate)
                use_pulse = False
                if self.cfg.pulse_enabled and not single_side:
                    # Check if we're in a curve that needs pulse control
                    if (abs(theta_deg) > self.cfg.pulse_theta_threshold or
                        abs(lateral_px) > self.cfg.pulse_lateral_threshold):
                        use_pulse = True

                if use_pulse:
                    # Pulse mode: alternate between ON and OFF phases
                    if self._pulse_phase:
                        # ON phase
                        drive = self.cfg.pulse_drive_on * scale * self.cfg.forward_sign
                        self._pulse_counter += 1
                        if self._pulse_counter >= self.cfg.pulse_on_frames:
                            self._pulse_counter = 0
                            self._pulse_phase = False
                    else:
                        # OFF phase (coast)
                        drive = self.cfg.pulse_drive_off * self.cfg.forward_sign
                        self._pulse_counter += 1
                        if self._pulse_counter >= self.cfg.pulse_off_frames:
                            self._pulse_counter = 0
                            self._pulse_phase = True
                else:
                    # Normal continuous control
                    drive = base * scale * self.cfg.forward_sign
                    # Reset pulse state when not in curve
                    self._pulse_counter = 0
                    self._pulse_phase = True

                drive, steer = self._post_process(drive, steer)
                ...
                return drive, steer
```

**Explanation:**
- Lines 161-167: **Pulse activation decision:**
  - Only enable if `pulse_enabled` is True.
  - Disable when `single_side` is True (estimated lane is less reliable).
  - Activate when either:
    - `|theta_deg| > 25` degrees (significant heading error), OR
    - `|lateral_px| > 30` pixels (significant position error).
- Lines 169-183: **Pulse state machine:**
  - If in ON phase (`_pulse_phase = True`):
    - Set drive to 35% throttle.
    - Increment counter.
    - After 3 frames, switch to OFF phase.
  - If in OFF phase (`_pulse_phase = False`):
    - Set drive to 0% (coast).
    - Increment counter.
    - After 3 frames, switch back to ON phase.
- Lines 184-189: **Normal continuous control:**
  - When not in pulse mode, use calculated base speed.
  - Reset pulse state for next curve.
- Line 191: Apply post-processing (limits and smoothing).

### Lines 197-215: Hold and Search Modes

```python
        # ---------------- hold ----------------
        if mode == "hold":
            decay = self.cfg.hold_decay_per_frame ** max(0, int(lost_age))
            base = self._last_base * decay
            steer = self._last_steer * decay
            drive = base * scale * self.cfg.forward_sign
            drive, steer = self._post_process(drive, steer)
            self._store_debug(False, True, "hold", lateral_px, theta_deg,
                              0.0, 0.0, steer, drive, steer, soc, base, scale, lost_age)
            return drive, steer

        # ---------------- search ----------------
        base = _clip(self.cfg.search_speed, self.cfg.v_min, self.cfg.v_max) if not self.cfg.search_pivot else 0.0
        steer = abs(self.cfg.search_steer_const)  # constant right turn
        drive = base * scale * self.cfg.forward_sign
        drive, steer = self._post_process(drive, steer)
        self._store_debug(False, True, "search", lateral_px, theta_deg,
                          0.0, 0.0, steer, drive, steer, soc, base, scale, lost_age)
        return drive, steer
```

**Explanation:**
- Lines 198-206: **Hold mode:**
  - `decay = 0.9 ^ lost_age` - exponential decay based on how long lane is lost.
  - At lost_age=0: decay = 1.0 (100%).
  - At lost_age=10: decay = 0.9^10 = 0.35 (35%).
  - At lost_age=40: decay = 0.9^40 = 0.015 (1.5%).
  - Multiply last known base and steer by decay.
  - This gradually slows down while maintaining steering direction.
- Lines 208-215: **Search mode:**
  - If `search_pivot` is True: `base = 0.0` (rotate in place).
  - Otherwise: use `search_speed` for slow forward motion.
  - `steer = 0.6` radians (~34 degrees) - constant right turn.
  - This rotates the robot to search for the lane.

### Lines 217-230: Helper Methods

```python
    # ------------ helpers ------------
    def _post_process(self, drive: float, steer: float) -> Tuple[float, float]:
        """Apply limits and smooth."""
        drive = _clip(drive, -self.cfg.torque_limit, self.cfg.torque_limit)
        steer = _clip(steer, -self.cfg.steer_limit, self.cfg.steer_limit)
        return self._smooth(drive, steer)

    def _smooth(self, drive: float, steer: float) -> Tuple[float, float]:
        """IIR smoothing on output commands."""
        a = _clip(self.cfg.alpha_smooth, 0.0, 1.0)
        drive_s = (1 - a) * drive + a * self._prev_drive
        steer_s = (1 - a) * steer + a * self._prev_steer
        self._prev_drive, self._prev_steer = drive_s, steer_s
        return drive_s, steer_s
```

**Explanation:**
- Lines 218-222: **Post-processing:**
  - Clip drive to `[-torque_limit, +torque_limit]`.
  - Clip steer to `[-steer_limit, +steer_limit]`.
  - Apply smoothing.
- Lines 224-230: **IIR (Infinite Impulse Response) smoothing:**
  - `a = alpha_smooth = 0.5` in this config.
  - `output = (1 - a) * new_value + a * previous_value`
  - `output = 0.5 * new + 0.5 * old` - equal blend of new and old.
  - This creates a first-order low-pass filter that reduces jerky motion.
  - Store smoothed values for next iteration.

---

## 4. sliding_windows.py - Lane Detection

This module detects white lane lines using the sliding window algorithm.

### Lines 1-37: Header and Parameters

```python
# sliding_windows.py
# Standalone: Histogram-based Sliding Windows for WHITE lane (education-ready)

from dataclasses import dataclass
from PIL import Image
import numpy as np
import cv2, os, glob, csv, argparse
from typing import Optional

# ===== Parameters (adjust if needed) =====
ROI_TOP_FRAC  = 0.35       # ROI top (fraction of image height)
ROI_BOT_FRAC  = 0.88       # ROI bottom
NWINDOWS      = 12         # number of vertical windows
MARGIN        = 60         # half-width of each window [px]
MINPIX        = 50         # re-centering threshold
KERNEL        = 3          # morphology kernel size

# ===== Validation thresholds =====
MIN_POINTS_EACH_SIDE = 150  # Minimum points for valid lane per side
LATERAL_MAX_PX = 80.0       # Maximum acceptable lateral offset [px]
THETA_MAX_DEG = 75.0        # Maximum acceptable heading angle [deg]
LANE_WIDTH_PX = 100         # Estimated lane width for single-side fallback [px]
```

**Explanation:**
- Lines 11-16: **ROI (Region of Interest) parameters:**
  - `ROI_TOP_FRAC = 0.35` - start looking 35% down from top.
  - `ROI_BOT_FRAC = 0.88` - stop looking at 88% (near bottom).
  - This focuses on the relevant road area, ignoring sky and immediate foreground.
  - `NWINDOWS = 12` - divide ROI into 12 horizontal slices.
  - `MARGIN = 60` - each search window is 120px wide (±60 from center).
  - `MINPIX = 50` - need at least 50 white pixels to update window position.
- Lines 19-22: **Validation thresholds:**
  - `MIN_POINTS_EACH_SIDE = 150` - need 150+ points per lane line to be valid.
  - `LATERAL_MAX_PX = 80` - reject if lane center is >80px from image center.
  - `THETA_MAX_DEG = 75` - reject if heading error >75 degrees.
  - `LANE_WIDTH_PX = 100` - assumed lane width for single-side estimation.

### Lines 39-51: Result Data Structure

```python
@dataclass
class SWResult:
    ok: bool
    left_pts: Optional[np.ndarray]
    right_pts: Optional[np.ndarray]
    left_fit: Optional[np.ndarray]   # [a,b,c] for x = a*y^2 + b*y + c
    right_fit: Optional[np.ndarray]
    lateral_px: Optional[float] = None
    theta_deg: Optional[float] = None
    img_width: Optional[int] = None
    canvas_bgr: Optional[np.ndarray] = None
    single_side: bool = False
```

**Explanation:**
- Line 40: `ok` - True if lane was successfully detected.
- Lines 41-42: `left_pts`, `right_pts` - raw detected points for each lane line.
- Lines 43-44: `left_fit`, `right_fit` - polynomial coefficients `[a, b, c]`.
  - The polynomial is `x = a*y² + b*y + c` (quadratic in y, solves for x).
  - This allows curved lanes.
- Lines 45-46: `lateral_px`, `theta_deg` - computed lane center offset and heading.
- Line 47: `img_width` - image width for normalization.
- Line 48: `canvas_bgr` - debug visualization image.
- Line 49: `single_side` - True if one lane was estimated from the other.

### Lines 84-98: White Lane Binary Mask

```python
def white_binary(hsv: np.ndarray) -> np.ndarray:
    """
    White lane is assumed to be low saturation / high value.
    Extract by thresholding low S and high V in HSV.
    """
    S_MAX = 60
    V_MIN = 190
    lo = np.array([0,   0,   V_MIN], dtype=np.uint8)
    hi = np.array([180, S_MAX, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lo, hi)

    k = np.ones((KERNEL, KERNEL), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k, iterations=1)
    return mask
```

**Explanation:**
- Lines 89-90: **HSV thresholds for white:**
  - `S_MAX = 60` - saturation < 60 (low saturation = grayish/white).
  - `V_MIN = 190` - value > 190 (high brightness).
  - Hue is ignored (0-180) since white has no hue.
- Lines 91-92: Create lower and upper bounds for `cv2.inRange`.
- Line 93: `cv2.inRange` creates binary mask (255 where in range, 0 elsewhere).
- Lines 95-97: **Morphological operations:**
  - `MORPH_OPEN` - erosion followed by dilation. Removes small noise.
  - `MORPH_CLOSE` - dilation followed by erosion. Fills small gaps.
  - `k` is a 3x3 kernel.

### Lines 100-129: Main Function - Initial Setup

```python
def sliding_windows_white(pil_img: Image.Image, save_debug=True, src_path=None, return_canvas=False) -> SWResult:
    bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    H, W = bgr.shape[:2]
    y_top = int(H * ROI_TOP_FRAC)
    y_bot = int(H * ROI_BOT_FRAC)
    roi_bgr = bgr[y_top:y_bot, :]
    hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)

    # Debug canvas
    dbg = bgr.copy()
    cv2.rectangle(dbg, (0, y_top), (W, y_bot), (0, 0, 255), 2)   # ROI box
    cx = W // 2
    cv2.line(dbg, (cx, y_top), (cx, y_bot), (0, 255, 0), 2)      # image center line

    # Binary
    binary = white_binary(hsv)
    if np.count_nonzero(binary) < 300:
        # Not enough white pixels
        if save_debug:
            _save_debug_image(dbg, pil_img, src_path)
        return SWResult(False, None, None, None, None, ...)

    # Histogram-based initial positions
    half = binary[binary.shape[0] // 2 :, :]
    hist = np.sum(half, axis=0)
    midx = W // 2
    leftx_base  = np.argmax(hist[:midx]) if np.any(hist[:midx]) else midx // 2
    rightx_base = (np.argmax(hist[midx:]) + midx) if np.any(hist[midx:]) else ...
```

**Explanation:**
- Line 102: Convert PIL image to OpenCV BGR format.
- Lines 103-106: Extract ROI:
  - `y_top` and `y_bot` define vertical bounds.
  - `roi_bgr` is the cropped region.
- Line 107: Convert ROI to HSV color space for thresholding.
- Lines 110-113: Draw debug annotations:
  - Red rectangle showing ROI bounds.
  - Green vertical line at image center (reference).
- Lines 116-121: Create binary mask and check for minimum white pixels (300).
- Lines 124-128: **Histogram-based lane finding:**
  - Take bottom half of binary mask (`binary.shape[0] // 2 :`).
  - Sum columns (`axis=0`) to create histogram.
  - Find peak in left half = left lane starting position.
  - Find peak in right half = right lane starting position.
  - `np.argmax` returns index of maximum value.

### Lines 130-172: Sliding Window Loop

```python
    win_h = binary.shape[0] // NWINDOWS
    nonzero_y, nonzero_x = binary.nonzero()
    leftx_current, rightx_current = int(leftx_base), int(rightx_base)

    left_inds, right_inds = [], []

    # Sliding windows
    for win in range(NWINDOWS):
        win_y_low  = y_bot - (win + 1) * win_h
        win_y_high = y_bot - win * win_h
        ry_low  = win_y_low  - y_top
        ry_high = win_y_high - y_top

        lx_low, lx_high = leftx_current - MARGIN, leftx_current + MARGIN
        rx_low, rx_high = rightx_current - MARGIN, rightx_current + MARGIN

        cv2.rectangle(dbg, (lx_low, win_y_low), (lx_high, win_y_high), WIN_COLOR_LEFT, WIN_THICKNESS)
        cv2.rectangle(dbg, (rx_low, win_y_low), (rx_high, win_y_high), WIN_COLOR_RIGHT, WIN_THICKNESS)

        good_left = ((nonzero_y >= ry_low) & (nonzero_y < ry_high) &
                     (nonzero_x >= lx_low) & (nonzero_x < lx_high)).nonzero()[0]
        good_right = ((nonzero_y >= ry_low) & (nonzero_y < ry_high) &
                      (nonzero_x >= rx_low) & (nonzero_x < rx_high)).nonzero()[0]

        left_inds.append(good_left)
        right_inds.append(good_right)

        if len(good_left) > MINPIX:
            leftx_current = int(np.mean(nonzero_x[good_left]))
        if len(good_right) > MINPIX:
            rightx_current = int(np.mean(nonzero_x[good_right]))
```

**Explanation:**
- Line 131: `win_h` - height of each window in pixels.
- Line 132: Get coordinates of all nonzero (white) pixels.
- Line 133: Initialize current search positions.
- Lines 138-142: **Window coordinate calculation:**
  - Start from bottom (`win=0` is lowest).
  - `win_y_low` and `win_y_high` are in full-image coordinates.
  - `ry_low` and `ry_high` are relative to ROI top.
- Lines 144-145: Calculate window horizontal bounds (±MARGIN from current position).
- Lines 147-148: Draw window rectangles on debug image.
- Lines 150-153: **Find white pixels in each window:**
  - Boolean indexing: select pixels where y is in window AND x is in window.
  - `.nonzero()[0]` gets indices of True values.
- Lines 155-156: Accumulate indices for later.
- Lines 158-161: **Re-centering:**
  - If enough pixels found (>MINPIX), update window center to mean x position.
  - This allows the window to "follow" the lane line.

### Lines 173-203: Polynomial Fitting with Single-Side Fallback

```python
    left_inds  = np.concatenate(left_inds)  if len(left_inds)  else np.array([], dtype=int)
    right_inds = np.concatenate(right_inds) if len(right_inds) else np.array([], dtype=int)

    leftx  = nonzero_x[left_inds]
    leftyR = nonzero_y[left_inds]
    rightx = nonzero_x[right_inds]
    rightyR= nonzero_y[right_inds]
    lefty  = leftyR + y_top
    righty = rightyR + y_top

    # Fit polynomials with single-side fallback
    ok = False
    left_fit = right_fit = None
    single_side_mode = None

    left_valid = leftx.size >= MIN_POINTS_EACH_SIDE
    right_valid = rightx.size >= MIN_POINTS_EACH_SIDE

    if left_valid and right_valid:
        # Normal: both sides detected
        left_fit  = np.polyfit(lefty.astype(np.float32),  leftx.astype(np.float32),  2)
        right_fit = np.polyfit(righty.astype(np.float32), rightx.astype(np.float32), 2)
        ok = True
    elif left_valid and not right_valid:
        # Left only: estimate right lane
        left_fit = np.polyfit(lefty.astype(np.float32), leftx.astype(np.float32), 2)
        right_fit = left_fit.copy()
        right_fit[2] += LANE_WIDTH_PX  # Shift right by lane width
        single_side_mode = "left_only"
        ok = True
    elif right_valid and not left_valid:
        # Right only: estimate left lane
        right_fit = np.polyfit(righty.astype(np.float32), rightx.astype(np.float32), 2)
        left_fit = right_fit.copy()
        left_fit[2] -= LANE_WIDTH_PX  # Shift left by lane width
        single_side_mode = "right_only"
        ok = True
```

**Explanation:**
- Lines 163-164: Concatenate all window indices into single arrays.
- Lines 166-171: Extract actual x,y coordinates of detected points.
- Line 171: Convert ROI-relative y to full-image y.
- Lines 178-179: Check if each side has enough points.
- Lines 181-185: **Normal case (both sides):**
  - `np.polyfit(y, x, 2)` - fit quadratic polynomial.
  - Returns `[a, b, c]` where `x = a*y² + b*y + c`.
- Lines 186-192: **Left-only fallback:**
  - Fit polynomial to left lane.
  - Copy coefficients for right lane.
  - Add `LANE_WIDTH_PX` to the constant term `c` (shifts curve right).
  - Mark as single-side mode.
- Lines 193-201: **Right-only fallback:**
  - Same logic but shift left by subtracting lane width.

### Lines 225-269: Lateral and Theta Calculation

```python
    if ok and (left_fit is not None) and (right_fit is not None):
        y_center = (y_top + y_bot) // 2

        def x_centerline(y):
            xl = np.polyval(left_fit,  y)
            xr = np.polyval(right_fit, y)
            return 0.5 * (xl + xr)

        # Lateral (difference from image center)
        x_center_lane = float(x_centerline(y_center))
        lateral = x_center_lane - (W / 2)

        # Heading angle (upward finite diff)
        h = 1.0
        xc_up = float(x_centerline(y_center - h))
        xc_dn = float(x_centerline(y_center + h))
        dxdy_up = (xc_up - xc_dn) / (2.0 * h)
        theta_rad = np.arctan(dxdy_up)
        theta_deg = float(np.degrees(theta_rad))

        # Anomaly filtering
        is_anomaly = (abs(lateral) > LATERAL_MAX_PX or abs(theta_deg) > THETA_MAX_DEG)
```

**Explanation:**
- Line 227: `y_center` - middle of the ROI for measurements.
- Lines 229-232: `x_centerline(y)` - helper function:
  - Evaluate left polynomial at y: `xl = a*y² + b*y + c`.
  - Evaluate right polynomial at y: `xr`.
  - Return average: lane center.
- Lines 235-236: **Lateral offset:**
  - Get x position of lane center at `y_center`.
  - Subtract image center (W/2).
  - Positive = lane center is to the right = robot is left of center.
- Lines 239-244: **Heading angle calculation:**
  - Finite difference approximation of derivative.
  - `xc_up` - lane center slightly above.
  - `xc_dn` - lane center slightly below.
  - `dxdy_up = (xc_up - xc_dn) / (2*h)` - how much x changes per unit y.
  - `theta_rad = arctan(dxdy_up)` - convert slope to angle.
  - Positive = lane is tilted right = robot should turn right.
- Line 247: **Anomaly detection:**
  - If lateral or theta exceeds thresholds, mark as anomaly.
  - Anomalies are rejected to prevent erratic behavior.

---

## 5. perception_Startsignal.py - Start Signal Detection

This module detects the F1-style start lights to determine when to begin racing.

### Lines 1-10: Helper Function

```python
# perception_startsignal.py
# Detects red lamp pattern from a given RGB image (PIL) to determine race start.

from PIL import Image

def is_red(pixel, red_thresh=140, green_thresh=130, blue_thresh=130):
    """Returns True if the given pixel is considered 'red' based on RGB thresholds."""
    r, g, b = pixel
    return r > red_thresh and g < green_thresh and b < blue_thresh
```

**Explanation:**
- Lines 6-9: `is_red()` function:
  - A pixel is "red" if:
    - Red channel > 140 (bright red).
    - Green channel < 130 (not too much green).
    - Blue channel < 130 (not too much blue).
  - This simple heuristic works well for bright red signal lights.

### Lines 11-71: Main Detection Function

```python
def detect_start_signal(img):
    """
    Analyze a given PIL image to detect red start lamps.
    Returns True only once right after all lamps turn off (after being lit).
    """
    if not hasattr(detect_start_signal, 'ready_to_go'):
        detect_start_signal.ready_to_go = False

    try:
        width, height = img.size
        top = 0
        bottom = int(height * 0.3)

        # Define 3 rectangular regions (start lamps) on the top part of the image
        lamp_positions = [
            (int(width * 0.35), int(width * 0.5)),
            (int(width * 0.55), int(width * 0.7)),
            (int(width * 0.75), int(width * 0.9))
        ]

        red_count = 0
        for left, right in lamp_positions:
            red_pixels = 0
            total_pixels = 0
            for y in range(top, bottom):
                for x in range(left, right):
                    pixel = img.getpixel((x, y))
                    if is_red(pixel):
                        red_pixels += 1
                    total_pixels += 1
            ratio = red_pixels / total_pixels
            if ratio > 0.03:
                red_count += 1

        # All 3 red lights are ON → prepare to go
        if red_count == 3:
            detect_start_signal.ready_to_go = True
            return False

        # All lights OFF & ready flag was set → GO!
        if red_count == 0 and detect_start_signal.ready_to_go:
            print("[StartSignal] GO!!")
            detect_start_signal.ready_to_go = False
            return True

        return False
```

**Explanation:**
- Lines 16-17: **Function-level state:**
  - Python trick: attach attribute to the function itself.
  - `ready_to_go` persists between calls.
  - Initialized to False on first call.
- Lines 21-22: Focus on top 30% of image (where lights appear).
- Lines 25-29: **Define lamp regions:**
  - Three horizontal bands corresponding to three start lights.
  - Each spans roughly 15% of image width.
- Lines 31-43: **Count red pixels in each lamp region:**
  - Loop through every pixel in the region.
  - Count how many are "red" according to threshold.
  - If ratio > 3%, consider that lamp "on".
  - Increment `red_count` for each lit lamp.
- Lines 46-48: **Sequence detection (lights on):**
  - When all 3 lights are on, set `ready_to_go = True`.
  - But don't return True yet - wait for lights to go off.
- Lines 51-55: **Sequence detection (lights off):**
  - When lights go off AND `ready_to_go` was set, return True (GO!).
  - Reset `ready_to_go` to prevent multiple triggers.
- Line 57: Default return False (no signal change).

---

## 6. perception_Lane.py - Red Lane Detection

This module detects red lane markings (alternative to white lane detection).

### Lines 17-41: HSV Color Thresholds for Red

```python
# === HSV ranges for RED (two ranges due to hue wrap) ===
RED1_LO, RED1_HI = (0, 80, 60),   (10, 255, 255)
RED2_LO, RED2_HI = (170, 80, 60), (180, 255, 255)

# === ROI (relative heights) ===
ROI_TOP_FRAC  = 0.45
ROI_BOT_FRAC  = 0.90

def _make_red_mask(hsv_roi: np.ndarray) -> np.ndarray:
    m1 = cv2.inRange(hsv_roi, np.array(RED1_LO), np.array(RED1_HI))
    m2 = cv2.inRange(hsv_roi, np.array(RED2_LO), np.array(RED2_HI))
    mask = cv2.bitwise_or(m1, m2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5,5), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5,5), np.uint8))
    return mask
```

**Explanation:**
- Lines 18-19: **Red color in HSV is split:**
  - Hue 0-10: red-orange.
  - Hue 170-180: red-magenta.
  - Red "wraps around" at hue=0/180, so we need two ranges.
  - Saturation > 80 (colorful, not gray).
  - Value > 60 (not too dark).
- Lines 22-23: ROI from 45% to 90% of image height.
- Lines 25-31: `_make_red_mask()`:
  - Create two masks for the two red ranges.
  - OR them together to get all red pixels.
  - Morphological cleanup with 5x5 kernel.

### Lines 43-93: Detection Function

```python
def detect_from_pil(pil_img: Image.Image, save_debug: bool=False) -> LaneObs:
    bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    h, w, _ = bgr.shape
    roi_top = int(h * ROI_TOP_FRAC)
    roi_bot = int(h * ROI_BOT_FRAC)

    roi = bgr[roi_top:roi_bot, :]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    mask = _make_red_mask(hsv)
    M = cv2.moments(mask)
    area = M["m00"]

    # confidence: how much of ROI is red
    conf = 0.0 if area <= 0 else float(min(1.0, area / (mask.size * 0.15)))

    if area < 1000:  # too few pixels
        return LaneObs(False, 0.0, 0.0, conf)

    # centroid (x only)
    cx = M["m10"] / area
    lateral = (cx - (w/2)) / (w/2)  # normalize to -1..1

    # Get centroid y for angle calculation
    pts = cv2.findNonZero(mask)
    cy_roi = float(pts[:, :, 1].mean()) if pts is not None else (roi_bot - roi_top) * 0.5
    cy = roi_top + cy_roi

    # Angle from robot center to lane centroid
    x0, y0 = (w / 2.0), float(roi_bot)
    dx = cx - x0
    dy_up = (y0 - cy)
    heading_deg = float(np.degrees(np.arctan2(dx, dy_up + 1e-6)))

    return LaneObs(True, float(lateral), heading_deg, conf)
```

**Explanation:**
- Lines 53-54: `cv2.moments(mask)` - computes image moments.
  - `M["m00"]` = total area (sum of all pixel values = number of white pixels * 255).
  - `M["m10"]` = sum of x*pixel_value.
  - `M["m01"]` = sum of y*pixel_value.
- Line 58: Confidence = how much of ROI is red (capped at 1.0).
- Lines 60-61: If less than 1000 red pixels, detection failed.
- Lines 64-65: **Centroid calculation:**
  - `cx = M["m10"] / M["m00"]` = weighted average x position.
  - `lateral = (cx - center) / half_width` = normalized offset (-1 to +1).
- Lines 68-70: Get y coordinate of centroid for angle calculation.
- Lines 73-76: **Heading angle:**
  - `x0, y0` = robot position (bottom center of ROI).
  - `dx` = horizontal distance to centroid.
  - `dy_up` = vertical distance (positive = upward).
  - `arctan2(dx, dy_up)` = angle from vertical.
  - Positive = centroid is to the right = turn right.

---

## 7. status_Robot.py - Robot State Machine

A simple state machine for tracking robot operating mode.

```python
# status_Robot.py
# Maintains global state of the robot

# State constants
WAITING_START = 0     # Waiting for the start signal
RUN_STRAIGHT = 1      # Currently running on a straight segment
RUN_CORNER = 2        # Placeholder for future cornering logic

# Global state variable
robot_state = WAITING_START

def get_state():
    """Returns the current global robot state."""
    return robot_state

def set_state(state):
    """Sets the current global robot state."""
    global robot_state
    robot_state = state
```

**Explanation:**
- Lines 5-7: State constants as integers:
  - `WAITING_START = 0` - robot is waiting for GO signal.
  - `RUN_STRAIGHT = 1` - robot is driving.
  - `RUN_CORNER = 2` - reserved for future use.
- Line 10: Global state variable, initialized to WAITING_START.
- Lines 12-19: Getter and setter functions.
  - `set_state` uses `global` to modify module-level variable.

---

## 8. debug_utils.py - Debug Visualization

This module provides utilities for creating debug overlay images.

### Lines 44-73: Steer Vector Visualization

```python
def _draw_steer_vector(img: np.ndarray, drive_tq: float, steer_ang: float, *, radius: int = 34, pad: int = 16) -> None:
    """
    Draw a "steer control vector" in the top-right.
    - Angle = steer_ang (rad, + is right turn)
    - Length = abs(drive_tq) (0..1)
    - Color: green for forward, red for reverse
    """
    h, w = img.shape[:2]
    cx = w - pad - radius
    cy = pad + radius

    # Guide circle + cross (light gray)
    cv2.circle(img, (cx, cy), radius, (210, 210, 210), 1, cv2.LINE_AA)
    cv2.line(img, (cx - radius, cy), (cx + radius, cy), (210, 210, 210), 1, cv2.LINE_AA)
    cv2.line(img, (cx, cy - radius), (cx, cy + radius), (210, 210, 210), 1, cv2.LINE_AA)

    drive = float(drive_tq)
    steer = float(steer_ang)
    length = min(1.0, abs(drive))

    r_pix = int(radius * length)
    dx = int(r_pix * math.sin(steer))
    dy = int(-r_pix * math.cos(steer))  # up is negative in image coords

    color = (0, 255, 0) if drive >= 0 else (0, 0, 255)  # green forward, red reverse

    cv2.line(img, (cx, cy), (cx + dx, cy + dy), (0, 0, 0), 3, cv2.LINE_AA)
    cv2.line(img, (cx, cy), (cx + dx, cy + dy), color, 2, cv2.LINE_AA)
```

**Explanation:**
- Lines 52-54: Position the indicator in top-right corner.
- Lines 56-58: Draw reference circle and crosshairs in light gray.
- Lines 60-62: Calculate vector length based on drive magnitude.
- Lines 64-65: **Vector direction:**
  - `dx = r * sin(steer)` - horizontal component (right for positive steer).
  - `dy = -r * cos(steer)` - vertical component (up for forward, negative in image coords).
- Line 67: Color: green for forward, red for reverse.
- Lines 69-70: Draw with black outline for visibility.

---

## 9. Linetrace_white.py - Legacy PID Control

An older, simpler approach using basic image processing and PID control.

### Lines 11-20: PID Parameters

```python
# PID control parameters
Kp = 0.005
Ki = 0.0
Kd = 0.001

# Motion control parameters
FORWARD = 0.3
TURN_GAIN = 1.0
A_WEIGHT = 0.5
B_WEIGHT = 0.5
```

**Explanation:**
- Lines 11-14: PID gains (note: Ki=0, so effectively PD control).
- Line 17: `FORWARD = 0.3` - base forward speed.
- Line 18: `TURN_GAIN = 1.0` - multiplier for turning.
- Lines 19-20: Weights for blending deviation and angle errors.

### Lines 33-48: Centroid and Angle Detection

```python
def detect_gravity_and_angle(binary, roi_top):
    """Extracts the centroid and angle of a white line region from a binary mask."""
    coords = cv2.findNonZero(binary)
    if coords is None or len(coords) < 5:
        return None, None, None

    x = coords[:, 0, 0]
    y = coords[:, 0, 1] + roi_top

    x_c = np.mean(x)
    y_c = np.mean(y)

    poly = np.polyfit(x, y, 1)
    theta_rad = np.arctan(poly[0])

    return (x_c, y_c), theta_rad, poly
```

**Explanation:**
- Line 35: Get coordinates of all white pixels.
- Lines 39-42: Calculate centroid (mean x, mean y).
- Lines 44-45: Fit a line (`y = mx + b`) to the points.
  - `poly[0]` = slope m.
  - `arctan(m)` = angle of the line.

### Lines 50-78: Main Control Logic

```python
def run(soc, pil_img):
    global prev_error, integral

    if soc < 0.2:
        return 0.0, 0.0

    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    roi_top = int(height * 0.4)
    roi_bottom = int(height * 0.9)
    roi = gray[roi_top:roi_bottom, :]

    _, binary = cv2.threshold(roi, 200, 255, cv2.THRESH_BINARY)

    center = width // 2
    gravity_point, target_angle, poly = detect_gravity_and_angle(binary, roi_top)

    if gravity_point is None:
        return 0.5, 0.5

    deviation = (gravity_point[0] - center) / center
    theta_norm = target_angle / np.radians(45.0)
    correction = A_WEIGHT * deviation + B_WEIGHT * theta_norm
    turn = TURN_GAIN * correction

    left = np.clip(FORWARD - turn, -1.0, 1.0)
    right = np.clip(FORWARD + turn, -1.0, 1.0)
```

**Explanation:**
- Lines 53-54: Low battery protection - stop if SOC < 20%.
- Lines 56-62: Image preprocessing - convert to grayscale, extract ROI.
- Line 64: Simple threshold - pixels > 200 become white.
- Lines 72-75: **Control calculation:**
  - `deviation` = normalized horizontal error.
  - `theta_norm` = normalized angle error (relative to 45°).
  - `correction` = weighted sum of both errors.
  - `turn` = final turning command.
- Lines 77-78: **Differential drive output:**
  - `left = FORWARD - turn` - slower when turning right.
  - `right = FORWARD + turn` - faster when turning right.
  - Note: This is for differential drive, not steer-type control.

---

## 10. Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CONTROL LOOP (20Hz)                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  INPUT: Camera Image (RGB, 224x224)                                     │
│  INPUT: Battery SOC (0.0-1.0)                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: Start Signal Detection                                        │
│  ─────────────────────────────────                                      │
│  perception_Startsignal.py                                              │
│                                                                         │
│  - Scan top 30% of image for red lights                                 │
│  - State machine: wait for 3 lights ON, then 0 lights                   │
│  - Output: start_go = True/False (latched)                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: Lane Perception (only after start_go)                         │
│  ───────────────────────────────────────────────                        │
│  sliding_windows.py                                                     │
│                                                                         │
│  1. Extract ROI (35%-88% of image height)                               │
│  2. Create binary mask (white = low saturation, high value)             │
│  3. Histogram to find lane starting positions                           │
│  4. Sliding windows (12 windows, ±60px margin)                          │
│  5. Polynomial fit: x = a*y² + b*y + c                                  │
│  6. Single-side fallback if one lane missing                            │
│  7. Calculate lateral_px and theta_deg                                  │
│  8. Anomaly rejection if values too extreme                             │
│                                                                         │
│  Output: SWResult(ok, lateral_px, theta_deg, single_side, ...)          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 3: Mode Decision                                                 │
│  ─────────────────────────                                              │
│  rule_based_input.py                                                    │
│                                                                         │
│  if lane_ok:                                                            │
│      lane_mode = "normal", lost_age = 0                                 │
│  else:                                                                  │
│      lost_age += 1                                                      │
│      if lost_age <= 40: lane_mode = "hold"                              │
│      else: lane_mode = "search"                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 4: Driver Model                                                  │
│  ─────────────────────────                                              │
│  driver_model.py                                                        │
│                                                                         │
│  NORMAL MODE:                                                           │
│    1. Normalize: lateral_n = lateral_px / (image_width/2)               │
│    2. Convert: theta_rad = radians(theta_deg)                           │
│    3. Steer: steer = k_theta * theta_rad + k_lateral * lateral_n        │
│    4. Speed: base = v_max * (1 - |steer|/steer_limit * 0.7)             │
│    5. Pulse: if |theta| > 25° → alternate ON/OFF throttle               │
│    6. SOC scale: drive = base * soc_scale                               │
│                                                                         │
│  HOLD MODE:                                                             │
│    decay = 0.9^lost_age                                                 │
│    drive = last_base * decay                                            │
│    steer = last_steer * decay                                           │
│                                                                         │
│  SEARCH MODE:                                                           │
│    drive = 0 (pivot in place)                                           │
│    steer = 0.6 rad (constant right turn)                                │
│                                                                         │
│  POST-PROCESS:                                                          │
│    Clip to limits, apply IIR smoothing                                  │
│                                                                         │
│  Output: (driveTorque, steerAngle)                                      │
└──────────────────────────────────────────────────────────��──────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  OUTPUT: Control Command                                                │
│  ────────────────────────                                               │
│  {                                                                      │
│    "type": "control",                                                   │
│    "robot_id": "R1",                                                    │
│    "driveTorque": 0.450,    # -1.0 to +1.0                              │
│    "steerAngle": 0.150      # -0.785 to +0.785 rad (±45°)               │
│  }                                                                      │
│                                                                         │
│  → Sent to Unity via WebSocket                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Key Algorithms Summary

### 1. Sliding Window Lane Detection
- Start from histogram peaks at bottom of image
- Move windows upward, following white pixels
- Fit quadratic polynomial to detected points
- Handle single-side detection with lane width estimation

### 2. Proportional Steering Control
- `steer = k_theta * theta + k_lateral * lateral`
- Combines heading error and position error
- Gains tuned for stability (k_theta=0.45, k_lateral=0.30)

### 3. Adaptive Speed Control
- Base speed reduced in curves: `v = v_max * (1 - steer_cost * 0.7)`
- Minimum speed floor prevents stalling
- SOC scaling maintains performance at low battery

### 4. Pulse Throttle for Curves
- Mimics human "tap-tap" technique
- Alternates between 35% and 0% throttle
- Activated when |theta| > 25° or |lateral| > 30px
- Helps navigate tight corners without overshooting

### 5. Lane-Loss Recovery
- Hold mode: exponentially decay speed/steer for 2 seconds
- Search mode: pivot in place with constant right turn
- Prevents crashes when lane temporarily lost

---

*Document generated for VRR Beta 1.3 - January 2026*
