# aira — Virtual Robot Race

**Race your Algorithm. Challenge the World.**

The official simulator for **[aira](https://aira-race.com)** — Autonomous Intelligence Racing Arena.
Train your AI algorithm, race against others, and climb the global leaderboard.

> **Ready to compete?**
> → **[Sign up & view competitions at aira-race.com](https://aira-race.com)**
> → **[Global Leaderboard](https://aira-race.com/competitions)**

> ⚠️ **Platform**: Windows only (so far). Mac/Linux support is planned for a future release.

---

## What is aira?

**aira** (Autonomous Intelligence Racing Arena) is a competition platform for Explainable Physical AI.
This repository contains the **official simulator** — a beginner-friendly environment where you can:

- Race robots with realistic car physics (torque steer dynamics)
- Train and test AI models using PyTorch
- Compete on the global leaderboard at [aira-race.com](https://aira-race.com)
- Learn autonomous driving through hands-on experimentation

2 robots race head-to-head on a closed circuit. You can drive manually, replay recorded runs, use rule-based algorithms, or let a neural network AI take the wheel.

**Platform**: [aira-race.com](https://aira-race.com) — register, join competitions, and track your ranking.

---

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/aira-race/virtual-robot-race.git
cd virtual-robot-race
```

### 2. Install Python Dependencies
```bash
# Recommended: Python 3.12+
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Or simply double-click **`setup_env.bat`** for automatic setup!

### 3. Download AI Model (Optional)
If you want to use AI control mode (MODE_NUM=4):
- [Download model.pth from Google Drive](https://drive.google.com/file/d/1NDL3A2lWDgXdy7OUWctyoR35jtYqthWD/view?usp=sharing)
- Place it in `Robot1/models/model.pth`

### 4. Run the Simulator
```bash
python main.py
```

Unity will auto-launch and the race begins!

---

## Step-by-Step Lessons

New to aira? The lessons walk you through everything from environment setup to submitting your first race result — in English and Japanese.

→ **[Open the Lessons index (docs/README.md)](docs/README.md)**

---

## Setup Guide

### Python Installation
* Download and install **Python 3.12+ (64-bit)**:
  [https://www.python.org/downloads/](https://www.python.org/downloads/)

  **Important**: During installation, check "Add Python to PATH"

  > Tested with Python 3.12 and 3.13. Python 3.10/3.11 may work but are not officially supported.

### Quick Setup (Recommended)
Simply double-click `setup_env.bat`.

This will automatically:
- Create virtual environment (.venv)
- Activate it
- Install all required packages

### Manual Setup (Alternative)
If you prefer manual control or setup_env.bat doesn't work:

1. Open **Command Prompt** (not PowerShell)
2. Navigate to the repository root:
   ```bash
   cd path\to\virtual-robot-race
   ```
3. Run these commands one by one:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

You'll see `(.venv)` at the start of your command line when the virtual environment is active.

### GPU Acceleration (Recommended for AI Training)

If you have an **NVIDIA GPU** and want faster AI model training, install the CUDA-enabled PyTorch:

```bash
.venv\Scripts\activate
pip uninstall torch torchvision -y
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
```

**Verify GPU is detected:**
```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

> **No GPU?** The default CPU version works fine for inference (running the AI). GPU mainly speeds up training.

> **CUDA version**: This project uses CUDA 12.4. If you have an older GPU or driver, try `cu118` instead of `cu124`.

---

## Project Structure

```
virtual-robot-race/
├── main.py                  # Main launcher
├── config.txt               # Global settings (which robots to activate)
├── requirements.txt         # Python dependencies
├── setup_env.bat            # Quick setup script
│
├── scripts/                 # Shared Python modules
│   ├── websocket_client.py  # Communication with Unity
│   ├── config_loader.py     # Configuration loader
│   ├── data_manager.py      # Training data manager
│   ├── make_video.py        # Video creation utility
│   └── smartphone_server.py # Smartphone controller server
│
├── Robot1/                  # First robot configuration
│   ├── robot_config.txt     # (legacy — no longer used; see config.txt)
│   ├── keyboard_input.py    # Manual control (MODE_NUM=1)
│   ├── table_input.py       # CSV playback (MODE_NUM=2)
│   ├── table_input.csv      # Recorded control data
│   ├── rule_based_input.py  # Rule-based control (MODE_NUM=3)
│   ├── inference_input.py   # AI inference engine (MODE_NUM=4)
│   ├── ai_control_strategy.py
│   ├── model.py             # Neural network model definition
│   ├── rule_based_algorithms/
│   │   ├── driver_model.py
│   │   ├── perception_Lane.py
│   │   ├── perception_Startsignal.py
│   │   └── ...
│   ├── data_interactive/    # Real-time data (auto-generated, gitignored)
│   ├── models/
│   │   └── model.pth        # AI model (download separately)
│   └── training_data/       # Recorded runs for AI training
│       └── run_YYYYMMDD_HHMMSS/
│           ├── images/
│           ├── metadata.csv
│           └── unity_log.txt
│
├── Robot2/                  # Second robot (same structure as Robot1)
│
├── Windows/                 # Unity executable
│   ├── aira_Beta_1.7.exe
│   └── ...
│
├── docs/                    # User-facing documentation
│   ├── lessons_JP/
│   └── lessons_EN/
│
└── colab/                   # Google Colab training notebooks
    └── train_on_colab.ipynb
```

---

## Configure Your Robots

All settings are in a single **`config.txt`** file in the repository root.

```ini
# ===== Player =====
NAME=aira_Racer_0001       # Up to 16 characters: A-Z, a-z, 0-9, _ (underscore)
COMPETITION_NAME=Tutorial   # Competition ID or "Tutorial" for practice

# ===== Network =====
HOST=localhost
PORT=12346

# ===== System =====
ACTIVE_ROBOTS=1,2    # Which robots to activate (comma-separated, max 2)
HEADLESS=0           # 0=Show launcher GUI, 1=Start immediately
DEBUG_MODE=0         # 0=Auto-launch Unity (recommended), 1=Manual (advanced)

# ===== Data & Race =====
DATA_SAVE=0          # 1=Save images+CSV, 0=Don't save
RACE_FLAG=0          # 1=Submit result to leaderboard, 0=Practice only
X_POST_FLAG=0        # 1=Post result to X (Twitter), 0=Don't post

# ===== Robot Modes =====
R1_MODE_NUM=4        # Robot1 mode: 1=keyboard, 2=table, 3=rule_based, 4=ai, 5=smartphone
R2_MODE_NUM=4        # Robot2 mode
```

> **Note**: `robot_config.txt` files (Robot1/, Robot2/) are no longer used. All configuration is unified in `config.txt`.

---

## Control Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Keyboard** (1) | Manual WASD control | Practice and data collection |
| **CSV Playback** (2) | Replay recorded runs | Reproduce results |
| **Rule-Based** (3) | Lane detection + algorithms | Traditional robotics approach |
| **Neural Network AI** (4) | PyTorch deep learning | End-to-end autonomous driving |
| **Smartphone** (5) | Phone as wireless gamepad | Intuitive dual-joystick control |

### 1. Keyboard Control (MODE_NUM=1)
- **W**: Accelerate
- **Z**: Brake/Reverse
- **J**: Steer left
- **L**: Steer right
- **I** or **M**: Steer center (neutral)

### 5. Smartphone Controller (MODE_NUM=5)
1. Set `R1_MODE_NUM=5` in `config.txt`
2. Run `python main.py` — a QR code will appear
3. Scan the QR code with your phone
4. Use dual virtual joysticks to control your robot
   - **Left joystick**: Throttle (up=forward, down=reverse)
   - **Right joystick**: Steering (left/right)
5. Press both L+R buttons simultaneously to start

> Your phone and PC must be on the same WiFi network.

---

## Data Recording (DATA_SAVE=1)

When `DATA_SAVE=1` is enabled, race data is automatically saved to the `training_data` folder.

### Folder Structure
```
Robot1/training_data/
└── run_YYYYMMDD_HHMMSS/
    ├── images/              # Camera RGB images (JPEG)
    ├── metadata.csv         # Telemetry data
    └── unity_log.txt        # Unity debug log
```

### metadata.csv Columns

| Column | Description |
|--------|-------------|
| `id` | Tick ID (1 tick = 50ms) |
| `session_time_ms` | Game internal timer (ms) |
| `race_time_ms` | Time since GO signal (ms) |
| `filename` | Image filename linked to this tick |
| `soc` | Battery State of Charge (0.0–1.0) |
| `drive_torque` | Drive torque command |
| `steer_angle` | Steering angle (rad, positive=right) |
| `status` | `StartSequence`, `Lap0`–`Lap3`, `Finish`, `Fallen`, `FalseStart`, `BatteryDepleted`, `ForceEnd` |
| `pos_z` | Forward position (m) |
| `pos_x` | Lateral position (m) |
| `yaw` | Heading angle (deg, 0=start, positive=right) |
| `pos_y` | Vertical position (m) |
| `collision_type` | `wall`, `robot`, `both`, or empty |
| `collision_penalty` | SOC penalty this frame (0.0–1.0) |
| `collision_target` | `Wall`, `Robot1`, `Robot2`, etc. |

---

## Collision Penalty System

Collisions drain the robot's battery (SOC) proportional to impact energy, teaching AI models to avoid crashes.

```
Penalty = k * E * R

k = basePenaltyRate / maxSpeed²    (normalization factor)
E = |velocity|²  or  |V_rel|²     (collision energy)
R = responsibility ratio            (0.0 to 1.0)
```

| Collision Type | Energy (E) | Responsibility (R) |
|----------------|------------|---------------------|
| Wall | Own speed² | 1.0 (always 100%) |
| Robot-to-Robot | Relative speed² | 0.5 + 0.5 * dot(V, -normal) |

**Default parameters**: basePenaltyRate=0.20, maxSpeed=5.0 m/s, cooldown=1.0s

**Example**: Hitting a wall at 3.0 m/s → E=9.0, penalty = 0.008 × 9.0 × 1.0 = 7.2% SOC loss

---

## Racing Scenarios

### Solo Practice
```ini
# config.txt
NAME=YourName
ACTIVE_ROBOTS=1
R1_MODE_NUM=1
RACE_FLAG=0          # Practice — no result submission
```

### Head-to-Head Race
```ini
# config.txt
NAME=YourName
COMPETITION_NAME=Race_XXXXXX   # Must match a registered competition ID
ACTIVE_ROBOTS=1,2
R1_MODE_NUM=1        # You drive Robot1
R2_MODE_NUM=4        # AI opponent
RACE_FLAG=1          # Submit fastest result to leaderboard
```

### Algorithm Competition
```ini
# Compare two approaches
NAME=YourName
ACTIVE_ROBOTS=1,2
R1_MODE_NUM=3        # Rule-based
R2_MODE_NUM=4        # Neural network
RACE_FLAG=0
```

---

## AI Training Workflow

1. **Collect Data**: Drive manually (MODE_NUM=1) with DATA_SAVE=1
2. **Train Model**: Use local GPU or Google Colab (`colab/train_on_colab.ipynb`)
3. **Deploy**: Copy trained `model.pth` to `Robot*/models/`
4. **Race**: Run with MODE_NUM=4 (AI control)
5. **Iterate**: Analyze results and improve

---

## Sharing Your Results

After completing a race with `RACE_FLAG=1`:

1. A **Post Confirmation Panel** appears — review your result and click **POST**
2. The fastest result across all active robots is submitted to the leaderboard
3. Visit [https://aira-race.com/](https://aira-race.com/) to see your ranking
4. Share your achievement on X (Twitter)
5. Challenge other racers to beat your time!

> Tip: Set `RACE_FLAG=0` during practice to avoid posting incomplete runs.
> Note: Competition mode requires your `NAME` to be pre-registered in the competition sheet. Use `COMPETITION_NAME=Tutorial` for open practice.

---

## Community & Support

- **Platform & Leaderboard**: [aira-race.com](https://aira-race.com)
- **Competitions**: [aira-race.com/competitions](https://aira-race.com/competitions)
- **YouTube**: [@RaceYourAlgo](https://www.youtube.com/@RaceYourAlgo)
- **X (Twitter)**: [@RaceYourAlgo](https://x.com/RaceYourAlgo)
- **Issues**: [GitHub Issues](https://github.com/aira-race/virtual-robot-race/issues)

---

## Tested Environments

| Device | CPU | GPU | RAM | Status |
|--------|-----|-----|-----|--------|
| Dev PC | Intel Core i5-12450H | RTX 3060 Laptop | 16GB | Smooth |
| Surface Laptop 2 | Intel Core i5 (8th Gen) | Intel UHD 620 | 8GB | Works |

> Windows only. Mac/Linux support coming soon.

---

## Tips for Better Racing

- **Practice first**: Use `RACE_FLAG=0` to learn the track
- **Watch replays**: Set `AUTO_MAKE_VIDEO=1` to analyze your driving
- **Tune your AI**: Training data is saved in `Robot*/training_data/`
- **Compare modes**: Race different control methods against each other
- **Monitor battery**: Collisions drain SOC — smooth driving preserves energy

---

## Troubleshooting

### Unity won't launch
- Set `DEBUG_MODE=1` in config.txt and launch Unity manually
- Check that `Windows/aira_Beta_1.7.exe` exists

### Robot doesn't move
- Verify `ACTIVE_ROBOTS` includes your robot number
- Check that the robot's `MODE_NUM` is set correctly
- Try keyboard control (MODE_NUM=1) first

### AI model not found
- Download `model.pth` from Google Drive
- Place it in `Robot*/models/model.pth`
- Make sure the filename is exactly `model.pth`

### Results not posting
- Check your internet connection
- Verify `RACE_FLAG=1` in config.txt
- Ensure `NAME` is 1–16 characters (A-Z, a-z, 0-9, underscore only)
- For competition mode: verify your `NAME` is registered in the competition sheet
- Make sure to click **POST** on the confirmation panel after the race

---

**Ready to race? Run `python main.py` and start your engines!**

---

## Version History

### Version 1.7 (2026-03-15)
- **New**: aira HUD redesign — status panel (PLAYER/COMP/MODE/LAP/SOC/STATUS), race timer, camera view decoration with SOC bar, corner-bracket reticle
- **New**: GAS (Google Apps Script) backend v2 — tutorial and competition result posting via WebApp URL
- **New**: Post confirmation panel — operator confirms before submitting results to leaderboard
- **New**: Competition mode — player verification against Competition_Index sheet before race start
- **Change**: Unified config — all settings moved from `Robot1/robot_config.txt` to single `config.txt`
- **Change**: `COMP_NAME` renamed to `COMPETITION_NAME`; default value is `Tutorial`
- **Change**: `NAME` now accepts underscores (`_`), up to 16 characters
- **Change**: Only the fastest result per race is submitted (previously all robots posted individually)
- **Rebrand**: Executable renamed to `aira_Beta_1.7.exe`

### Version 1.6 (2026-02-28)
- **New**: Tail lamp controller with shader — hue reflects steering direction, brightness reflects throttle, blink on reverse

### Version 1.5 (2026-02-08)
- **New**: Collision penalty system — collisions drain battery (SOC) proportional to impact energy
  - Wall collision: 100% self-responsibility, penalty based on speed squared
  - Robot-to-robot collision: responsibility split based on velocity direction
  - 1-second cooldown prevents double-counting from physics bounces
  - Formula: `Penalty = k * E * R` where k=normalization, E=energy, R=responsibility
- **New**: Collision data logged per-frame in metadata.csv (`collision_type`, `collision_penalty`, `collision_target`)
- **New**: Battery depletion status — robots with empty battery become obstacles on track

### Version 1.4 (2026-01-17)
- **New**: Offline RL training pipeline (DAgger+, AWR)

### Version 1.3 (2026-01-11)
- **New**: Smartphone controller mode (MODE_NUM=5)
- **New**: PanelManager for dynamic camera panel layout

### Version 1.2 (2026-01-10)
- **Fix**: Training data image/metadata alignment (328-frame offset resolved)

### Version 1.1 (2025-12-13)
- **New**: Real-time Input Vector Scope visualization
- **New**: Rule-Based autonomous driving achieves 2-lap goal
