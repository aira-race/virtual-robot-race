# Virtual Robot Race - Alpha Version

### Build and Race Your Own AI!

Welcome to the **Alpha version** of Virtual Robot Race!
This guide helps you set up the race simulator on your Windows PC and control your robot using Python.

You can manually drive the robot, replay pre-recorded torque data, or try rule-based and AI-controlled driving.

> **Note**: The Alpha version uses differential drive (tank-style steering). For the latest version with realistic car physics, 2-robot racing, and more features, see [Project_Beta](../Project_Beta/README.md).

---

## Overview

This guide walks you through:

1. Downloading the app from GitHub
2. Installing Python and required libraries
3. Understanding the file structure
4. Running the simulator and choosing control modes

---

## Step 1: Download the App

Clone or download the repository:

* GitHub: [https://github.com/AAgrandprix/virtual-robot-race](https://github.com/AAgrandprix/virtual-robot-race)

```bash
git clone https://github.com/AAgrandprix/virtual-robot-race.git
```

Or download ZIP and extract it.

---

## Step 2: Install Python & Libraries

* Download and install **Python 3.10+ (64-bit)**:
  [https://www.python.org/downloads/](https://www.python.org/downloads/)

  **Important**: During installation, check "Add Python to PATH"

* Open Command Prompt or Terminal:

```bash
cd Project_Alpha

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## AI Model Download

The AI mode requires a trained model file `model.pth`.

> This file is **not included** in the repository due to GitHub's 100MB limit.

[Download model.pth from Google Drive](https://drive.google.com/file/d/19qWtxAC1ABYiK1CGDg9A0PDX67u39I_v/view?usp=sharing)

After downloading, place the file in:

```
Project_Alpha/models/model.pth
```

Make sure the filename is exactly `model.pth`.

---

## Step 3: Project Structure

```
Project_Alpha/
├── setup_env.bat
├── requirements.txt
├── main.py
├── websocket_server.py
├── config.py
├── config.txt
├── keyboard_input.py
├── table_input.py
├── table_input.csv
├── data_interactive/
├── rule_based_input.py
├── rule_based_algorithms/
│   ├── debug_utils.py
│   ├── driver_model.py
│   ├── Linetrace_white.py
│   ├── perception_Lane.py
│   ├── perception_Startsignal.py
│   ├── perception_trackposition.py
│   ├── sliding_windows.py
│   └── status_Robot.py
├── inference_input.py
├── models/
│   └── model.pth   # Download from Google Drive
├── make_video.py
├── data_manager.py
├── Windows/
│   ├── AAgp_test32.exe
│   └── ...
└── training_data/
    └── run_YYYYMMDD_HHMMSS/
        ├── images/
        ├── metadata.csv
        ├── table_input.csv
        └── UnityLog.txt
```

---

## Step 4: Run the Simulator

```bash
python main.py
```

* Unity will auto-launch.
* Press `q` to end the race anytime.

---

## Choose Your Control Mode

Edit `config.txt` to set your control method:

```ini
# 1 = keyboard (manual)
# 2 = table (CSV playback)
# 3 = rule_based (signal + line follow)
# 4 = ai (PyTorch model)
MODE_NUM=1
```

---

## Verified Test Environments

| Device | CPU | GPU | RAM | Status |
|--------|-----|-----|-----|--------|
| Dev PC | 12th Gen Intel Core i5-12450H | NVIDIA GeForce RTX 3060 Laptop | 16.00 GB | Smooth |
| Surface Laptop 2 | 8th Gen Intel Core i5 | Intel UHD Graphics 620 | 8GB | Works (AI OK) |

This Alpha version is verified on **Windows 11**.
Mac/Linux support is not yet available.

---

## Community & Support

* YouTube: https://www.youtube.com/@RaceYourAlgo
* Official Website: [https://virtualrobotrace.com](https://virtualrobotrace.com)
* GitHub Issues: [https://github.com/AAgrandprix/virtual-robot-race/issues](https://github.com/AAgrandprix/virtual-robot-race/issues)

---

Race your Algorithm. Challenge the World.
