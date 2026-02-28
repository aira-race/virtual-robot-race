# 7. How to Join the Race

You have developed your algorithm and AI model through the training sessions — now it's time to race.
There are two race formats: "Time Attack" and "Head-to-Head."

---

## 1. Time Attack (Single Robot)

First, try the Time Attack where you drive solo and aim for the fastest time over 2 laps.

### Step 1: Finish Your Algorithm / AI Model
Complete the rule-based algorithm or AI model you developed during training.

### Step 2: Configure Race Settings
Open `Robot1/robot_config.txt` and set the following two items.

#### Player Name
Set `NAME` to your player name (up to 10 alphanumeric characters) that will appear on the leaderboard. Choose a clear name that distinguishes you from other participants.

```ini
# Player name (up to 10 alphanumeric characters, used for leaderboard)
NAME=Player0000
```

#### Race Participation Flag
Change `RACE_FLAG` to `1`. Setting this to `1` registers your run result on the official leaderboard.

```ini
# Race participation flag:
# 1 = Participate in race (results will be posted)
# 0 = Test Run only (no results posted)
RACE_FLAG=1
```

### Step 3: Drive
Run `main.py` to start the Time Attack.
When you finish, your time is automatically registered on the leaderboard.

**Leaderboard:** [https://aira-race.com/](https://aira-race.com/)

---

## 2. Head-to-Head (Two Robots)

In the next training session, you will compete in direct head-to-head races.

### How to Submit
Compress your entire `Robot1` folder as a ZIP file and submit it to the designated location.

**Submission location:** (Will be announced later)

### Race Format
- Submitted programs will race two at a time.
- Grid positions are determined based on Time Attack results. The faster driver starts as **Robot1** (front grid position).

> **[Important] Robustness of Start Control**
> Robot1 and Robot2 see the start signal from different positions and angles.
> The key to winning is implementing a **robust** start detection logic that fires reliably from either grid position.

---

Now, race with your algorithm!
**Race your algorithm!**
