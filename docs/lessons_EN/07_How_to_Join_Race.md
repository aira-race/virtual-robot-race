# 7. How to Join the Race

You have developed your algorithm and AI model through the training sessions — now it's time to race.
There are two race formats: "Time Attack" and "Head-to-Head."

---

## 1. Time Attack (Single Robot)

First, try the Time Attack where you drive solo and aim for the fastest time over 2 laps.

### Step 1: Finish Your Algorithm / AI Model
Complete the rule-based algorithm or AI model you developed during training.

### Step 2: Configure Race Settings
Open `config.txt` in the repository root and set the following items.

#### Player Name
Set `NAME` to your player name that will appear on the leaderboard. Allowed characters: A-Z, a-z, 0-9, and underscore (`_`), up to 16 characters.

```ini
# Player name: alphanumeric and underscore, up to 16 characters (A-Z, a-z, 0-9, _)
NAME=aira_Racer_0001
```

#### Competition Name
Set `COMPETITION_NAME` to the competition ID you are joining. For practice, leave it as `Tutorial`.

```ini
# Competition name: must match a valid competition ID registered on the platform
COMPETITION_NAME=Tutorial
```

> **Note (for competition mode)**: When setting a real competition ID, your `NAME` must be pre-registered in the competition sheet. If not registered, an authentication error will appear before the race starts.

#### Race Participation Flag
Change `RACE_FLAG` to `1`. Setting this to `1` submits your result to the official leaderboard.

```ini
# Race participation flag:
# 1 = Submit result to leaderboard
# 0 = Test run only (no submission)
RACE_FLAG=1
```

### Step 3: Drive
Run `main.py` to start the Time Attack.
When you finish, a **Post Confirmation Panel** appears. Review your result and click **POST** to submit the fastest time to the leaderboard.

**Leaderboard:** [https://aira-race.com/](https://aira-race.com/)

---

## 2. Head-to-Head (Two Robots)

In the next training session, you will compete in direct head-to-head races.

### How to Submit
Compress your entire `Robot1` folder as a ZIP file and submit it to the designated location.

**Submission location:** Check the active competition page for the ZIP submission link: [https://aira-race.com/competitions](https://aira-race.com/competitions)

### Race Format
- Submitted programs will race two at a time.
- Grid positions are determined based on Time Attack results. The faster driver starts as **Robot1** (front grid position).

> **[Important] Robustness of Start Control**
> Robot1 and Robot2 see the start signal from different positions and angles.
> The key to winning is implementing a **robust** start detection logic that fires reliably from either grid position.

---

Now, race with your algorithm!
**Race your algorithm!**
