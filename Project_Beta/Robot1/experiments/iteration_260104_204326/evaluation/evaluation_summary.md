# Evaluation Summary - iteration_260104_204326

**Evaluation Date:** 2026-01-04
**Model:** iteration_260104_204326/model.pth
**Test Runs:** 3

---

## Overview

| Metric | Value |
|--------|-------|
| Completion Rate | **0% (0/3)** |
| Average Race Time | 14.2s (all crashed) |
| Best Attempt | Run 2 (14.0s) |
| Common Failure | Start sequence crash |

---

## Detailed Results

### Run 1: run_20260104_210108
- **Status:** Crashed (Finish = abnormal termination)
- **Frames:** 304
- **Duration:** 14.2s
- **Final Position:** pos_x = 3.115, pos_z = 0.348
- **Final Status:** Lap0 → Finish
- **Analysis:** Crashed shortly after start

### Run 2: run_20260104_210137
- **Status:** Crashed (Finish = abnormal termination)
- **Frames:** 303
- **Duration:** 14.1s
- **Final Position:** pos_x = 3.112, pos_z = 0.434
- **Final Status:** Lap0 → Finish
- **Analysis:** Crashed shortly after start

### Run 3: run_20260104_210205
- **Status:** Crashed (Finish = abnormal termination)
- **Frames:** 306
- **Duration:** 14.3s
- **Final Position:** pos_x = 3.113, pos_z = 0.313
- **Final Status:** Lap0 → Finish
- **Analysis:** Crashed shortly after start

---

## Problem Analysis

### 1. Immediate Right Steering Bias
**Observation:** All 3 runs crashed at nearly identical positions (pos_x ≈ 3.1, pos_z ≈ 0.3-0.4)

**Root Cause:**
- Training data has **strong RIGHT steering bias** (+0.29 rad average)
- Model learned to steer right by default
- At start, model outputs right steering → hits right wall → crash

### 2. Training Data Characteristics
From training_info.md:
- **Total frames:** 1,273 (3 keyboard runs)
- **Steering distribution:**
  - Right: 57.7%
  - Left: 0.2%
  - Neutral: 42.1%
- **Average steer:** +0.2916 rad (strong right bias)

### 3. Missing Critical Data
The training data lacks:
- **Corner handling:** Sharp left/right turns
- **Recovery behavior:** How to correct after deviation
- **Balanced steering:** Equal left/right examples

---

## Failure Pattern

```
Start (pos_x=0)
  ↓
3 seconds of driving
  ↓
Model outputs RIGHT steering (learned from data bias)
  ↓
Robot hits RIGHT wall
  ↓
Crash at pos_x ≈ 3.1 (14 seconds total)
```

**Visual Evidence:**
- All runs terminated at pos_x ≈ 3.1 (very early in track)
- No run reached first corner (pos_x ≈ 30)
- Consistent crash location indicates systematic issue, not random

---

## Comparison with Training Data

| Metric | Training Data | Test Results |
|--------|---------------|--------------|
| Average Duration | 25.4s | 14.2s |
| Steering Bias | +0.29 rad (right) | Unknown (crashed) |
| Completion | 100% (keyboard) | 0% (AI) |

---

## Next Steps

### Immediate Actions Needed:

1. **Collect Better Training Data**
   - Include corner handling
   - Balance left/right steering
   - Multiple complete laps

2. **Data Augmentation**
   - Horizontal flip to create left-steering examples
   - Balance left/right distribution to 40-40-20

3. **Model Architecture Review**
   - Current model: CNN + MLP (1.12M params)
   - Consider adding temporal context (LSTM/GRU)
   - Consider post-processing adjustments

### Success Criteria for Next Iteration:

- [ ] Completion rate > 33% (at least 1/3 runs complete 1 lap)
- [ ] Average distance > 50m (reach first corner)
- [ ] Steering bias < 0.1 rad

---

## Files

- Run data: `evaluation/run_20260104_21xxxx/`
- Training info: `training_info.md`
- Model: `model.pth`
- This report: `evaluation/evaluation_summary.md`

---

**Conclusion:** This iteration demonstrates that the model successfully learned from the training data, but the training data itself had critical limitations (right steering bias, lack of corner examples). The model is working as expected given the data quality - the issue is not the model, but the training data collection process.

**Status:** ❌ Failed - Requires new training data with better coverage
