# 3. Manual Control

In this lesson, you will launch `main.py` and practice driving the robot with your keyboard.

## 1. Prerequisites

Before starting the lesson, check and modify two configuration files. The format follows the code block style used in `README.md`.

### 1. Select the Robot to Drive (`config.txt`)
Edit `config.txt` in the project root folder.
For this session, practice with a single robot by setting it as follows:

```ini
# config.txt
ACTIVE_ROBOTS=1
```

### 2. Robot-Specific Settings (`Robot1/robot_config.txt`)
Edit `robot_config.txt` in the `Robot1` folder.
The settings for keyboard control with log saving are:

```ini

# Player name (up to 10 alphanumeric characters, used for leaderboard)
NAME=YourName    # Change this to your own name

# Robot1/robot_config.txt
# Control mode:
# 1 = keyboard
# 2 = table (CSV playback)
# 3 = rule_based (autonomous lane following)
# 4 = ai (neural network inference)
# 5 = smartphone (smartphone controller via QR code)
MODE_NUM=1

# Data saving:
# 1 = Save CSV and JPEG images during run (also auto-creates MP4 video)
# 0 = Do not save data (faster, less disk usage, no video)
# Note: Video settings (FPS, etc.) are fixed in Python code for advanced users
DATA_SAVE=1

# Race participation flag:
# 1 = Participate in race (results will be posted)
# 0 = Test Run only (no results posted)
RACE_FLAG=0

```
> Be sure to change `YourName` to your own name.

> If you are unsure how to configure this, refer to the README or ask the Q&A system.

## 2. Basic Rules

Let's review the basic race rules.

- **Start:** Three red signals light up, then all go out. The lights going out is the start signal.
- **False Start:** Moving before the start signal results in a false start and disqualification.
- **Laps:** Complete 2 laps of the course; your total time is what counts.
- **Wrong-way driving:** Driving the course in reverse will deduct 1 from your lap count.
- **Battery (SOC):** Driving consumes battery. When SOC (State of Charge) reaches 0%, the robot can no longer move.
- **Collision:** Colliding with walls or other robots incurs a penalty that reduces SOC.
- **Course Out:** Falling off the course results in disqualification.
- **Time Up:** Failing to complete 2 laps within 90 seconds also results in disqualification.

## 3. Keyboard Controls

- **Accelerate / Reverse:** `W` / `Z`
- **Steer (left/right):** `J` / `L`
- **Center steering:** `I`, `M`
    - *Note: Releasing `J` or `L` will automatically return the steering to center, but `I` or `M` will center it instantly.*

## 4. Reading the Screen

### Camera View
When the screen is split, the left side is Robot1's camera view and the right side is Robot2's.

### Target Display
The circle on screen is the "target." It visualizes keyboard input (`W, Z, J, L`) as XY coordinates.
For example, with full forward torque and centered steering, the target moves to coordinates (0, 1).

### Tail Lamp on the Robot
This is an important interface that communicates your inputs (throttle, steering, reverse) to the robot behind you. It is not just decorative — it serves as a "visual log" relevant to race strategy.

- **Color (Hue):** Indicates steering direction.
    - **Straight:** Base color
    - **Left/Right:** Color shifts continuously in the direction of the turn.

- **Light height (gauge):** Indicates the strength of forward acceleration (torque).
    - **Throttle OFF:** Light is off.
    - **Throttle ON:** Gauge extends from bottom to top proportional to throttle input.

- **Blinking:** The most important warning — indicates the robot is reversing.
    - While reversing, the gauge is always **at maximum** and **blinks periodically**.
    - Note: While reversing, the **color still changes** according to steering direction.

## 5. Training Tasks

Work through the following steps to get comfortable with manual control.

1.  **One lap with Robot1:** Start with just Robot1 (single mode) and drive one lap around the course.
2.  **One lap with Robot2:** Next, try one lap with just Robot2 (single mode).
3.  **Experience failures:** Try out various disqualification scenarios — false starts, course outs, battery drain from collisions, etc.
4.  **Race alongside the AI:** Set Robot2 to AI mode, then chase it as Robot1 (keyboard mode).
5.  **Time attack:** Finally, go back to single mode (Robot1) and challenge everyone to the fastest time!
