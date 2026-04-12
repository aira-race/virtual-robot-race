# 6. AI Mode: Imitation Learning and Neural Networks

In this lesson, **you will train an AI to drive and let it run autonomously.**
It may sound difficult, but the essence of what you are doing is simple.
Make active use of an AI assistant (such as Gemini Code Assist) here as well.

**Learning goals:**
- Understand where and how "inference" and "training" happen
- Experience the steps to create an AI model through imitation learning
- Feel the difference in training cost between local and Google Colab
- Understand the concept of reinforcement learning and its role in this system

---

## 1. First, Run the Robot in AI Mode

Run `start.bat` to open the launcher and set the following:

| Setting | Value |
|---------|-------|
| **Active** | `1` |
| **R1 mode** | `ai` |

Click **START**.

### 1.1 Prepare the Sample Model

AI mode requires a trained model file (`model.pth`).
The sample model is included in the repository — confirm that `Robot1/models/model.pth` exists.

### 1.2 Run It

Run `start.bat`. The following log will appear in the terminal:

```
[R1 Inference] Using device: cpu   (or cuda)
[R1 Inference] Model loaded from ...\Robot1\models\model.pth
[R1 Inference] Waiting for start signal... (Strategy: hybrid)
[R1 Inference] RACE STARTED! (Strategy: hybrid)
[R1 Inference] Drive=+0.523, Steer=-0.031rad(-1.8deg), SOC=1.00
```

> **Observation points:**
> - How did the robot drive?
> - The `Drive=` and `Steer=` values change every 20 fps (50 ms).
> - Depending on the model quality, it is normal if it does not drive well.

---

## 2. How Inference Works (`inference_input.py`)

Look at `Robot1/inference_input.py`. Ask your AI assistant:

```
What does inference_input.py do?
```

---

### 2.1 The Core Inference Code

At the heart of the file are just a few lines of code:

```python
# Prepare input tensors
image_tensor = _transform(pil_img).unsqueeze(0).to(_device)  # [1, 3, 224, 224]
soc_tensor = torch.tensor([[soc]], dtype=torch.float32).to(_device)  # [1, 1]

# Run inference
with torch.no_grad():
    output = _model(image_tensor, soc_tensor)
    raw_drive = output[0, 0].item()   # drive_torque
    raw_steer = output[0, 1].item()   # steer_angle
```

**That is all.** Two pieces of data go in, two come out. This is MIMO.

---

### 2.2 Model Structure (`model.py`)

The neural network (`DrivingNetwork`) has a simple structure:

```
Input ①: RGB image 224×224      → CNN (4 conv layers + GlobalAvgPool) → 256-dim vector
                                                                          ↓ concat
Input ②: SOC (1 float)  ─────────────────────────────────────────────→ 257-dim vector
                                                                          ↓ MLP (fully connected)
Output: [drive_torque, steer_angle] (2-dim)
```

> **Note**: CNN (Convolutional Neural Network) extracts features from images.
> It converts visual information — like "the course curves right" or "the white line is shifted to the left" — into numbers.

---

### 2.3 Hybrid Mode vs. Pure E2E Mode

This system has two modes (configured in `ai_control_strategy.py`):

| Mode | Start Detection | Driving Control | Characteristics |
|------|----------------|----------------|----------------|
| **hybrid** (default) | Rule-based | AI | Start signal detection handled by reliable rules |
| **pure_e2e** | AI | AI | Fully delegated to AI (start signal is also learned) |

> There is no need to make AI learn things that can be reliably handled by rules.
> "Use rules for deterministic tasks, use AI for tasks that are hard to judge" is the practical approach.

---

## 3. Training an AI Model

### 3.1 What Is "Imitation Learning"?

The learning method used in this system is **Imitation Learning**.

1. A human (you) drives using the keyboard
2. The data — "image + SOC → throttle + steering" — is recorded during that run
3. The AI learns the pattern: "A human would do this in response to this image"

In other words, **the AI learns to imitate your driving.**
If you want an AI that drives well, you need to give it data from good driving.

> **Important**: This training does not happen in real-time during a race.
> The flow is: collect driving data → **train offline** → run with the trained model.

---

### 3.2 Training-Related File Structure

```
Robot1/
├── model.py                     ← Neural network definition (do not modify)
├── models/
│   └── model.pth                ← The trained model to use (place it here)
│
├── training_data/               ← Data collected by keyboard driving (saved with DATA_SAVE=1)
│   ├── run_20260216_094415/
│   │   ├── images/
│   │   └── metadata.csv
│   └── run_.../
│
├── ai_training/                 ← Training scripts
│   ├── train.py                 ← Main training script
│   ├── run_pipeline.py          ← Iterative training pipeline management
│   ├── run_scorer.py            ← Quality scoring for driving data
│   ├── run_iteration.py         ← Execute one iteration
│   ├── create_iteration.py      ← Create iteration folder
│   └── analyze.py               ← Data analysis tool
│
└── experiments/                 ← Training results storage (.gitignore excluded)
    └── iteration_[timestamp]/   ← One training attempt
        ├── data_sources/        ← Copy of data used for training
        ├── model.pth            ← Model produced by this attempt
        ├── model_best.pth       ← Model with the lowest validation loss
        ├── training_log.csv     ← Loss per epoch
        └── dataset_manifest.json← Statistics of the dataset used
```

---

### 3.3 Local Training Steps

**Step 1: Collect data**

Run `start.bat` to open the launcher and set the following, then drive in keyboard mode.

| Setting | Value |
|---------|-------|
| **Active** | `1` |
| **R1 mode** | `keyboard` |
| **Data save** | `ON` |

After driving, a `Robot1/training_data/run_[datetime]/` folder is created.
At least 3 runs worth of data tend to produce better training results.

**Step 2: Run training**

In the `Robot1/` directory, run:

```bash
python ai_training/train.py --data training_data
```

Training starts and loss is displayed per epoch:

```
Epoch   1/100 | Train: 0.045312 | Val: 0.048201 | LR: 1.00e-04 | 12.3s
Epoch   2/100 | Train: 0.038441 | Val: 0.041023 | LR: 1.00e-04 | 12.1s ✓ NEW BEST
...
⏹️  Early stopping triggered at epoch 47
Best validation loss: 0.012345
Model saved to: experiments/iteration_[timestamp]/model.pth
```

**Step 3: Place the model**

Copy the generated model to the `models/` folder. Replace `[timestamp]` with the actual folder name.

```bash
cp experiments/iteration_[timestamp]/model_best.pth models/model.pth
```

> **Tip**: `model_best.pth` (the model with the lowest validation loss) tends to perform better than `model.pth` (the final epoch model).

**Step 4: Run in AI mode**

Set **R1 mode=`ai`** in the launcher and click **START**.

---

### 3.4 Filtering Training Data

`train.py` filters training data using the `status` column in `metadata.csv`:

| Used | Excluded |
|------|----------|
| `Lap0`, `Lap1`, `Lap2`, `Finish` | `StartSequence`, `Fallen`, `FalseStart`, `ForceEnd` |

Data from during the countdown or after a fall is excluded because it does not represent "correct driving."

---

## 4. Training with Google Colab

### 4.1 Why Use Colab?

If your local PC has no GPU, training can take a very long time (tens of minutes to hours).
Using Google Colab's GPU, **the same data can train in just a few minutes to about 10 minutes**.

This is called "**training cost**." Experience the performance difference of a GPU and the meaning of paying for cloud compute.

---

### 4.2 Training Steps on Colab

`colab/train_on_colab.ipynb` is the instruction notebook. The flow is as follows:

**1. Files to prepare on Google Drive**

Upload the following to `/MyDrive/virtual-robot-race/` on Google Drive:

| File/Folder | Drive path |
|-------------|-----------|
| `Robot1/training_data/` | `/MyDrive/virtual-robot-race/training_data/` |
| `Robot1/model.py` | `/MyDrive/virtual-robot-race/model.py` |

**2. Colab settings**

- Runtime → Change runtime type → Select **GPU** (T4 is sufficient)

**3. Run cells in order**

| Cell | Content |
|------|---------|
| Cell 1 | Mount Google Drive and set paths |
| Cell 2 | Verify PyTorch and CUDA |
| Cell 3 | Create iteration folder |
| Cell 4 | Auto-copy `run_` folders from `training_data/` to `data_sources/` |
| Cell 5 | Generate `dataset_manifest.json` (sample count, completion judgment, etc.) |
| Cell 6 | Initialize model, create DataLoader, configure Data Augmentation |
| Cell 7 | Training loop (up to 100 epochs, with early stopping) |
| Cell 8 | Generate training curve graph and display summary |

**4. Download model.pth**

After training is complete, download `iteration_[timestamp]/model.pth`.
Overwrite it as `Robot1/models/model.pth` locally to complete the process.

---

## 5. Batch Learning vs. Real-Time Learning

> **Important**: The imitation learning in this system is **batch learning (offline learning)**.

```
Batch learning (imitation learning):
  Keyboard driving → data collection → offline training → place model → test run → repeat

Real-time reinforcement learning:
  While driving → compute reward → update model on the fly → keep driving
```

With the MIMO configuration (image + SOC → torque + steering), **position information (pos_x, pos_z) cannot be obtained in real-time**, because `metadata.csv` is only delivered after the race ends. This places constraints on real-time reinforcement learning that requires sophisticated reward design using position information.

---

## 6. More Advanced Learning: DAgger and Reward Design

### 6.1 Limitations of Imitation Learning

The initially trained model has a weakness: when it encounters **situations the human never drove through**, it cannot handle them correctly.

For example:
- A situation where it drifts slightly off course → it doesn't know how to recover because there is no human data for it
- It gradually drifts further with each lap → even if the first lap is fine, it breaks down

This is called **"Distribution Shift."**

---

### 6.2 DAgger: Improve Through Iterative Data Collection

The technique that solves this problem is **DAgger (Dataset Aggregation)**.
`run_pipeline.py` implements this pipeline.

```
DAgger Cycle:

  1. Train initial model from human data
         ↓
  2. Run the model in AI mode (rollout)
         ↓
  3. Add the AI's run data to the human data
         ↓
  4. Retrain on the combined data (stronger as data grows)
         ↓
  Return to 2 (repeat)
```

By continually adding to the training data situations the AI has not yet encountered, it gradually becomes an AI that can "handle any situation."

**Usage:**

```bash
# Check the current state of the pipeline
python ai_training/run_pipeline.py status

# Execute the next step (training or rollout)
python ai_training/run_pipeline.py next
```

---

### 6.3 Reward Design: Quantifying Data "Quality"

Rather than using all data from DAgger equally, there is a mechanism to **weight "good runs" more heavily and "bad runs" less heavily (or exclude them)**.

This is handled by `rl_reward.py` and `run_scorer.py`.

| File | Role |
|------|------|
| `rl_reward.py` | Defines the evaluation criteria (reward weights) for a run's "quality" |
| `run_scorer.py` | Analyzes `metadata.csv` and assigns a score to each run |
| `train.py` | Selects and weights data based on scores for training |

> **Note**: `rl_reward.py` is **not** for updating the model in real-time.
> It is a "scoring criteria" for scoring driving quality by reading `metadata.csv` after the race ends.
> In the current version, position information (pos_x, pos_z) cannot be obtained in real-time, so performing real-time reinforcement learning during a race is not practical.

---

### 6.4 What the Reward Evaluates

`rl_reward.py` and `run_scorer.py` currently implement the following evaluation criteria:

| Evaluation item | Content |
|-----------------|---------|
| Completion bonus | 2-lap finish (+1000), 1-lap finish (+400) |
| Time | Faster = higher score (baseline 120 sec, -2 per second) |
| SOC efficiency | Higher score for finishing with more battery remaining |
| Smoothness | Less steering jerk = higher score |
| Penalty | Fall (-500), forced termination (-100) |

By rewriting this "scoring criteria," you can change the definition of what constitutes "good driving."

Try discussing the following with your AI assistant:

```
Look at the scoring criteria in run_scorer.py and rl_reward.py.
For the goal of "completing 2 laps in the shortest time,"
do you have ideas for more effective scoring?
```

---

## 7. Training Tasks

### Task 1: Build Your Own AI Model from Keyboard Data (Local)

1. Set **R1 mode=`keyboard`, Data save=`ON`** in the launcher and drive for 3 runs
2. Run local training with `ai_training/train.py`
3. Place the generated `model.pth` in `models/` and set **R1 mode=`ai`** in the launcher to confirm it runs
4. Record how long training took (**Training Cost ①**)

### Task 2: Train the Same Data on Colab

1. Upload the same `training_data/` from Task 1 to Google Drive
2. Run training using `colab/train_on_colab.ipynb`
3. Record how long training took (**Training Cost ②**)

> **Think about it:**
> - How different was the training time between local and Colab?
> - Did you feel the difference in GPU performance and the value of paying for cloud?
> - How well did the AI trained on 3 runs of data drive?

### Task 3: Discuss How to Make It Even Stronger with the AI

Consult your AI assistant with the following:

```
Looking at how my current model drives, please propose ideas for improvement.
I'd like to discuss from these angles:
- How to increase and improve data quality (e.g., using only clean laps)
- What changes if we modify the model structure (model.py)?
- How should hybrid mode and Pure E2E be used?
- What changes if we use DAgger (collect → train → AI rollout → add data → retrain)?
- How does changing the scoring criteria in run_scorer.py affect data selection for training?
```

---
### Related Resources
- [05_Rule_Based_Control.md](05_Rule_Based_Control.md)
- [04_Log_and_Table_Mode.md](04_Log_and_Table_Mode.md)
- [Glossary](99_Glossary.md)

---

> **❓ Having trouble?**
> Paste your error message directly into [NotebookLM](https://notebooklm.google.com/notebook/ab916e69-f78b-47c3-9982-a5210a07d713) and ask for help.

---

⬅️ [Previous lesson: 05_Rule_Based_Control.md (Rule-Based Control)](05_Rule_Based_Control.md) ｜ ➡️ [Next lesson: 07_How_to_Join_Race.md (How to Join a Race)](07_How_to_Join_Race.md)
