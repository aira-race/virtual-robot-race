# 5. Rule-Based Control and AI Orchestration

In this lesson, you will tackle rule-based control — which may sound difficult.
However, you do not need to write Python programs from scratch. **The essence of this lesson is to use AI assistants (such as Gemini Code Assist) to the fullest to complete the tasks.**

**Learning goals:**
- Understand "what" this system controls (inputs, outputs, timing)
- Experience developing and improving control algorithms through Vibe Coding with an AI assistant
- Implement your own "winning strategy" and actually race with it

---

## 1. What Does This System Do? (MIMO Control)

### 1.1 Inputs and Outputs

This robot's control system has a structure called **MIMO (Multiple Input, Multiple Output)**.

| Type | Data | Details |
|------|------|---------|
| **Input ① Image** | RGB image | 224×224 pixel JPEG (from the robot's onboard camera) |
| **Input ② Battery** | SOC | Float value (e.g., `0.85`). Battery level from 0.0 to 1.0 |
| **Output ① Throttle** | `drive_torque` | Normalized torque from -1.0 to +1.0 |
| **Output ② Steering** | `steer_angle` | Steering angle ±0.524 rad (±30 degrees) |

From just **2 types of inputs**, the controller determines **2 types of outputs**.

### 1.2 What Must Be Achieved?

**Goal**: Complete 2 laps in the shortest time.

**Constraints:**

| Constraint | Details | Consequence if violated |
|------------|---------|------------------------|
| No false starts | Do not move before the GO signal | Immediate disqualification (FalseStart) |
| Stay on course | Do not fall off the course | Eliminated (Fallen) |
| Do not deplete battery | If SOC reaches 0, the robot cannot move | Becomes an obstacle (BatteryDepleted) |

> **Note**: Collisions with walls or other robots reduce SOC as a penalty, but do not cause immediate disqualification. However, they can be fatal if they accumulate.

### 1.3 Timing

The control loop runs at **20 fps (50 ms intervals)**. Every 50 ms, the image and SOC are acquired, an output is determined, and it is sent.

---

## 2. File Structure and Data Flow

### 2.1 Related Files

```
Robot1/
├── rule_based_input.py       ← Main control loop (the command center)
├── rule_based_algorithms/    ← Algorithm collection (edit these to develop)
│   ├── perception_Startsignal.py   Start signal detection
│   ├── sliding_windows.py          White line detection (sliding window method)
│   ├── driver_model.py             Steering and speed decision logic
│   ├── status_Robot.py             Robot state management
│   ├── perception_Lane.py          Lane recognition utilities
│   ├── perception_trackposition.py Track position estimation
│   ├── Linetrace_white.py          White line tracing implementation example
│   └── debug_utils.py              Debug image generation
└── data_interactive/         ← Real-time data directory (auto-generated, do not modify)
    ├── latest_RGB_a/         ← Latest image file (updated every 50 ms)
    ├── latest_RGB_b/
    └── latest_SOC.txt        ← Latest SOC value
```

### 2.2 Data Flow

```
Unity (Simulator)
  │  Updated every 50 ms
  ▼
data_interactive/
  latest_RGB_a or b  ← 224×224 JPEG
  latest_SOC.txt     ← Float text such as "0.850"
  │
  ▼ Read by rule_based_input.py
update() function
  ├─ Acquire and analyze image → compute lateral_px, theta_deg
  ├─ Acquire SOC
  ├─ driver_model.py determines drive_torque, steer_angle
  └─ Write to global variables driveTorque, steerAngle
  │
  ▼ Called by main.py
get_latest_command()  ← Output handling here
  └─ Returns {"type":"control", "driveTorque": ..., "steerAngle": ...}
  │
  ▼ Sent to Unity via WebSocket
```

### 2.3 Reading the Input

Inside the `update()` function in `rule_based_input.py`:

```python
soc = data_manager.get_latest_soc(robot_id)        # SOC: float 0.0 to 1.0
rgb_path = data_manager.get_latest_rgb_path(robot_id)  # Image path
pil_img = Image.open(rgb_path).convert("RGB")       # Load as PIL image
```

### 2.4 Writing the Output

Inside the `get_latest_command()` function in `rule_based_input.py`:

```python
def get_latest_command():
    return {
        "type": "control",
        "robot_id": robot_id,
        "driveTorque": round(float(driveTorque), 3),
        "steerAngle": round(float(steerAngle), 3),
    }
```

`update()` updates the global variables `driveTorque` / `steerAngle`, and `main.py` calls `get_latest_command()` to send them via WebSocket.

---

## 3. Run the Sample First

Change `R1_MODE_NUM` in `config.txt` to `3`.

```ini
R1_MODE_NUM=3
```

Launch `main.py` and run the robot.

> **Observation points:**
> - Did the robot drive the course autonomously?
> - Check the logs in the terminal (`Drive=`, `Steer=`, `LaneOK=`).
> - Look at the debug images saved in the `Robot1/debug/` folder. The white line detection is visualized there.

---

## 4. Understanding the Algorithm (With an AI Agent)

Now the real work begins. Ask your AI assistant the following prompts in order to understand the system.

**Step 1: Check the current directory**
```
Can you access the current directory?
```

**Step 2: Understand the entire system**
```
Read the .md and .py files in the directory and understand what kind of system and application this is.
```

**Step 3: Analyze the rule-based algorithm**
```
Understand the contents of the "rule_based_algorithms" folder and explain what controls are implemented in the sample.
```

> **Tip**: The AI assistant will read the code and explain it. Even if you cannot read the code yourself, the AI will tell you in plain language "what it is doing."

---

## 5. Algorithm Development: Plan Your Winning Strategy

### 5.1 Define Your Strategy

**You are now standing on the field of battle, together with an AI Agent.**

First, talk with the AI assistant to decide on a **strategy (policy)**.

```
Using this rule-based control system, propose a strategy for completing 2 laps in the shortest possible time.
Taking the winning conditions and constraints into account, tell me what parts of the current sample algorithm should be improved.
```

Example points to consider:
- How to go faster? (Raise `v_max`, adjust corner braking)
- Improve recovery when the lane is lost (`hold` / `search` logic)
- How to conserve SOC while driving? (Using `use_soc_scaling`)
- How to improve start signal detection accuracy?

### 5.2 Development Workflow

1. **Define policy**: Decide on an improvement policy through discussion with the AI assistant
2. **Implement**: Rewrite files in `rule_based_algorithms/` together with the AI assistant
3. **Test run**: Launch `main.py` and actually drive the robot
4. **Analyze**: Check results using terminal logs, debug images, and `metadata.csv`
5. **Iterate**: Improve and race again

The sample program is just a starting point — feel free to use it as a base, but don't be constrained by its philosophy. Skillfully guiding the AI assistant is part of an engineer's role.

> **Tip**: It's fine to use the sample as-is. Even tweaking a single parameter changes the driving behavior. Whether you make sweeping changes or fine-tune — the approach is yours to choose.

### 5.3 Key Parameters (`driver_model.py`)

Here are some parameters you can easily change:

| Parameter | Meaning | Default |
|-----------|---------|---------|
| `v_max` | Maximum speed (straight) | `0.55` |
| `v_min` | Minimum speed | `0.15` |
| `k_theta` | Gain on heading error | `0.45` |
| `k_lateral` | Gain on lateral offset | `0.30` |
| `alpha_smooth` | Output smoothing factor (larger = smoother) | `0.50` |
| `pulse_enabled` | Use pulse control in corners | `True` |
| `search_steer_const` | Steering angle when lane is lost [rad] | `0.6` |

### 5.4 Don't Forget Version Control

Now that control development has started, **commit and push to GitHub**.
Keeping a record of "versions you tried" lets you roll back when things go wrong.

```bash
git add Robot1/rule_based_algorithms/
git commit -m "Rule-based: v1.0 - First strategy"
git push
```

---

## 6. Training Tasks

### Task 1: Run the Sample and Change One Parameter

1. Run with `MODE_NUM=3` and record your time.
2. Change `v_max` in `driver_model.py` to `0.70` and run again.
3. What changed? Did it improve or worsen?

### Task 2: Improve with the AI Assistant

1. Share the result of Task 1 with the AI assistant and ask for the next improvement suggestion.
2. Implement the suggestion, run it, and compare.

### Task 3: Create Your Own "Winning Algorithm"

Create an algorithm that achieves the fastest time while respecting all constraints.
There is no single correct answer — experiment freely.

---
### Related Resources
- [04_Log_and_Table_Mode.md](04_Log_and_Table_Mode.md)
- [06_AI_Mode.md](06_AI_Mode.md)
- [Glossary](99_Glossary.md)
