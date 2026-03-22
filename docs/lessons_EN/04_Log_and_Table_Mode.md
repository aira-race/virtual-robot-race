# 4. Log Data Review and Table Mode

In this lesson, you will review the driving log (Log) saved during the previous manual control session, and learn about "Table Mode" — a mode that replays a run using that log data.

**Learning goals:**
- Understand the folder structure and contents of log data saved with `DATA_SAVE=1`
- Learn the meaning of the detailed driving data in `metadata.csv`
- Learn how to drive the robot using Table Mode (`MODE_NUM=2`) based on a CSV file
- Learn the basics of editing log data to create custom driving patterns

---

## 1. Reviewing Log Data

When you drive with `DATA_SAVE=1` set in the `03_Manual_Control` lesson, a folder named `run_[date]_[time]` is created inside `Robot1/training_data/`. This is a "log folder" containing all data from a single run.

### 1.1 Log Folder Structure
The log folder contains the following main files and folders:

- **`images/` folder**
  - All frames captured by the robot's camera during the run, saved as JPEG images.

- **`metadata.csv`**
  - The **most important data file** for a run. Every state of the robot during the run is recorded tick by tick (one tick = one simulation frame).

- **`output_video.mp4`**
  - A replay video automatically generated from the images in the `images/` folder.

- `UnityLog.txt`, `terminal_log.txt`
  - Detailed operation logs for debugging.
  - Contains logs from the Unity side and the Python side respectively.

---

### 1.2 Contents of `metadata.csv`
Open `metadata.csv` with a spreadsheet application like Excel or Google Sheets. The following **16 columns** appear from left to right.

#### Time / Identification

| Column | Contents |
|--------|----------|
| **`id`** | Sequential index for each tick. A unique number throughout the file. |
| **`session_time_ms`** | Elapsed time (ms) from the start of the start sequence. Counted even during the countdown. |
| **`race_time_ms`** | Elapsed time (ms) from the moment the "GO" signal fires. Stays `0` during the countdown. |
| **`filename`** | The corresponding image filename in the `images/` folder (e.g., `frame_000079.jpg`). |

#### Robot Operation / State

| Column | Contents |
|--------|----------|
| **`soc`** | Battery level (State of Charge). `1.0` = fully charged, `0.0` = empty. |
| **`drive_torque`** | Normalized drive torque. `+1.0` = maximum forward, `-1.0` = maximum reverse, `0.0` = stopped. |
| **`steer_angle`** | Front wheel steering angle (**in radians**). Range: **±0.524 rad (±30 degrees)**. Negative (`-`) = **left**, positive (`+`) = **right**. |
| **`status`** | A string representing the robot's state (see table below). |

**`status` value list:**

| Value | Meaning |
|-------|---------|
| `StartSequence` | Countdown to start |
| `Running` | Running |
| `Lap0` | Start of lap timing (used during training) |
| `Lap1` / `Lap2` ... | After passing a lap checkpoint |
| `Finish` | Completed the required number of laps |
| `FalseStart` | False start (moved before GO) → Disqualified |
| `Fallen` | Fell off the course → Eliminated |
| `BatteryDepleted` | Battery dead → Cannot move (becomes an obstacle) |
| `ForceEnd` | Forced termination |

#### Position / Orientation

> **Note**: The column order is `pos_z, pos_x, yaw, pos_y` — not alphabetical.
> **[Important]** `steer_angle` is in **radians**, but `yaw` is in **degrees**. Be careful when analyzing data.

| Column | Contents |
|--------|----------|
| **`pos_z`** | Z coordinate [m]. **Forward/backward** position (positive = course direction). |
| **`pos_x`** | X coordinate [m]. **Left/right** position (positive = right). |
| **`yaw`** | Yaw angle (heading direction) [**degrees**]. Forward direction = 0, clockwise = positive. |
| **`pos_y`** | Y coordinate [m]. **Up/down** position (positive = up). Below `-0.1 m` is judged as off-course. |

#### Error / Collision Information

| Column | Contents |
|--------|----------|
| **`error_code`** | Numeric error code. `999` during normal driving. |
| **`collision_type`** | Collision type for this tick: `"wall"`, `"robot"`, `"both"`, or `""` (no collision). |
| **`collision_penalty`** | Collision penalty rate applied at this tick (normally `0.0`). Immediately deducted from battery. |
| **`collision_target`** | Name of the collision target (e.g., `Robot2`, `Wall`). Empty if no collision. |

This file lets you analyze in detail "at what moment, with what input, where was the robot, and was there a collision."

---

## 2. Reproducing a Run in Table Mode

Table Mode (`MODE_NUM=2`) reads `drive_torque` and `steer_angle` values from top to bottom in `Robot1/table_input.csv` and drives the robot accordingly.
In other words, **the robot automatically drives according to a "blueprint" (table) you provide.**

### Format of `table_input.csv`
This file is very simple — it has only 3 columns:
- `time_id`: Sequential action number (integer starting from 0).
- `drive_torque`: Throttle input.
- `steer_angle`: Steering input.

---

## 3. Training Tasks

### Task 1: Reproduce a Run from Log Data

1.  **Prerequisites**
    - Set the following in `config.txt`:
      ```ini
      ACTIVE_ROBOTS=1
      R1_MODE_NUM=2
      ```

2.  **Create table data**
    - Open the log folder created during the previous practice session, and open `metadata.csv` in a spreadsheet application.
    - Select and copy the data in the `drive_torque` and `steer_angle` columns, up to the row where you finished (e.g., up to row 1000).

3.  **Edit `table_input.csv`**
    - Open `Robot1/table_input.csv` in a text editor or spreadsheet application.
    - **Delete all the old data in `drive_torque` and `steer_angle` (columns B and C), keeping column A (`time_id`) intact.**
    - Paste the copied `drive_torque` and `steer_angle` data into columns B and C.
    - **Fill column A (`time_id`) with sequential integers starting from `0`.** In Excel, enter `0` and `1`, then drag the fill handle to extend the sequence.
    - Save the file in CSV format.

4.  **Check the run**
    - Run `main.py`.
    - Confirm that the robot starts driving automatically according to the log you copied. Seeing your own keyboard inputs replayed may feel a little uncanny.

> **Think about it: Did it reproduce exactly?**
>
> Very few people will have replicated a clean lap. This is due to **latency**.
>
> The data you used as a log contains the command values the robot **actually received**. In Table Mode, that data is sent from top to bottom at **20 fps (50 ms intervals)**. The robot receives and acts on it.
>
> However, several "offsets" occur:
> - **Communication delay**: Transmission is not guaranteed to succeed, and packet arrival timing varies.
> - **Mechanical delay**: There is a slight time difference between instructing torque and the wheel actually rotating.
>
> This is the same in the real world. Simply "moving exactly as commanded" cannot handle external disturbances. This type of control is called **sequential control**.
>
> To move as intended, you need either carefully crafted command values with margin, or the **feedback control** you will learn next.

### Task 2: Edit the Driving Data (Advanced)

- Rewrite all `steer_angle` values in a specific section of `table_input.csv` to `0`, save, and observe how the robot moves (it should drive in a straight line).
- Try rewriting the `drive_torque` values for just the first curve to half their original value to simulate braking into the corner.

As you can see, Table Mode is highly effective for creating and testing precise autonomous driving patterns without AI or complex programs.

### Task 3: Visualize `metadata.csv`

Log data is just numbers, but **graphing it makes the run "visible."**
Try using Excel, Google Sheets, or Python (`pandas` + `matplotlib`) — whatever works for you.

---

#### Task 3-1: Draw the Driving Route (Scatter Plot)

Plot `pos_z` (horizontal axis) and `pos_x` (vertical axis) as a scatter plot.

> **Hint**: Set the X-axis to `pos_z` and the Y-axis to `pos_x`, and connect the data points with lines to get the driving trajectory.

- What shape of the course can you see?
- Where are the start and finish points?
- Are there sections where the trajectory drifts between laps?

---

#### Task 3-2: View Control Inputs Over Time (Line Chart)

Plot a line chart with `race_time_ms` on the horizontal axis and `drive_torque` and `steer_angle` on the vertical axis (overlapping both lines makes comparison easier).

> **Hint**: Rows where `race_time_ms` is `0` are during the countdown. Using only rows where the value is greater than `0` makes the actual race section easier to see.

- Where are the sections where you are pressing the throttle, and where are you easing off?
- When the steering angle is large, what is the relationship with `drive_torque`?
- Can you see a difference in control patterns between corners and straights?

---

#### Task 3-3: View Position and Heading Over Time (Line Chart)

Plot a line chart with `race_time_ms` on the horizontal axis and three lines: `pos_z`, `pos_x`, and `yaw`.

- Do `pos_z` and `pos_x` change at the same time, or do they alternate? (What does that mean?)
- Which sections of the scatter plot (Task 3-1) correspond to sharp changes in `yaw`?
- Compare the changes in `yaw` with the changes in `steer_angle` from Task 3-2. What relationship can you see?

---

### Related Resources
- [03_Manual_Control.md](03_Manual_Control.md)
- [05_Rule_Based_Control.md](05_Rule_Based_Control.md)
- [Glossary](99_Glossary.md)
