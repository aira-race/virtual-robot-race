# Iteration Workflow Guide
## AIモデル学習・評価の完全ワークフロー

**作成日:** 2026-01-04
**対象:** VRR Beta Project_Beta/Robot1

---

## 📋 概要

このガイドでは、AIモデルの学習から評価までを体系的に管理する新しいワークフローを説明します。

### 新しいツール

1. **create_iteration.py** - iterationフォルダの自動作成
2. **train_model_extended.py** - 拡張版学習スクリプト（自動記録・Loss曲線）

### Iteration管理の利点

✅ 完全なトレーサビリティ（どのデータで何を学習したか明確）
✅ 再現性の確保（データソースを完全コピー）
✅ 評価結果の一元管理
✅ 過去のiterationとの比較が容易

---

## 🚀 完全ワークフロー

### Phase 1: データ収集（マニュアル走行）

```bash
# 1. robot_config.txtでモードを設定
# MODE=keyboard

# 2. Unityを起動してマニュアル走行
cd Project_Beta
.venv/Scripts/python main.py

# 3. 3回走行（目標: 各60秒以上）
# → training_data/run_20260104_140000/
# → training_data/run_20260104_140300/
# → training_data/run_20260104_140500/
```

**走行のコツ:**
- スタートシグナルを待つ
- スムーズな操作を心がける
- 完走を目指す（クラッシュしてもOK、データとして有用）

---

### Phase 2: データ品質確認

```bash
cd Robot1

# 全runのステアリングバイアスを分析
../.venv/Scripts/python scripts/analyze_steering_bias.py --input ../training_data

# 出力例:
# Average steer: -0.0123 rad
# Left/Right/Neutral: 42.3% / 45.1% / 12.6%
# ✅ Good balance!
```

**確認ポイント:**
- 平均ステア: -0.05 ~ +0.05 rad が理想
- 左右比率: 40-50% 程度が理想
- 極端なバイアス（-0.2以上）のrunは除外を検討

---

### Phase 3: Iteration作成

#### 方法A: 全runを使用（推奨: 初回）

```bash
# 全runをコピーしてiteration作成
../.venv/Scripts/python scripts/create_iteration.py \
  --data ../training_data \
  --description "First 3 manual runs, keyboard control only"

# 出力例:
# ======================================================================
# Creating Iteration: iteration_260104_143052
# ======================================================================
#
# [1/5] Creating folder structure...
#   ✓ experiments/iteration_260104_143052
#   ✓ experiments/iteration_260104_143052/data_sources
#   ✓ experiments/iteration_260104_143052/evaluation
#   ✓ experiments/iteration_260104_143052/logs
#
# [2/5] Copying data sources...
#   Copying run_20260104_140000... ✓
#   Copying run_20260104_140300... ✓
#   Copying run_20260104_140500... ✓
#
#   Total runs copied: 3
#
# [3/5] Analyzing data statistics...
#   ✓ run_20260104_140000: 1523 frames, 75.2s, avg_steer=-0.052
#   ✓ run_20260104_140300: 1687 frames, 82.1s, avg_steer=+0.031
#   ✓ run_20260104_140500: 1313 frames, 68.9s, avg_steer=-0.018
#
#   Summary:
#     Total runs: 3
#     Total racing frames: 4,523
#     Average steer: -0.013 rad
#     Left/Right/Neutral: 42.1% / 45.3% / 12.6%
#
#   ✅ Good balance!
#
# [4/5] Creating training_config.yaml...
#   ✓ experiments/iteration_260104_143052/training_config.yaml
#
# [5/5] Creating README.md...
#   ✓ experiments/iteration_260104_143052/README.md
#
# ======================================================================
# ✅ Iteration created successfully!
# ======================================================================
#
# Iteration directory: experiments/iteration_260104_143052
#
# Next steps:
#   1. Review data_sources/ (3 runs)
#   2. Run training:
#      python train_model_extended.py \
#        --data experiments/iteration_260104_143052/data_sources \
#        --output experiments/iteration_260104_143052 \
#        --epochs 50
#   3. Evaluate with 3 test runs
```

#### 方法B: 特定のrunのみ使用

```bash
# 良質なrunのみ選択してiteration作成
../.venv/Scripts/python scripts/create_iteration.py \
  --data ../training_data \
  --runs run_20260104_140000 run_20260104_140300 \
  --description "Selected high-quality runs only"
```

---

### Phase 4: モデル学習

```bash
# 拡張版train_model.pyで学習実行
../.venv/Scripts/python train_model_extended.py \
  --data experiments/iteration_260104_143052/data_sources \
  --output experiments/iteration_260104_143052 \
  --epochs 50 \
  --device cuda

# 実行中の出力例:
# [Train] Using device: cuda
# [Train] Found 3 data directories:
#   - run_20260104_140000
#   - run_20260104_140300
#   - run_20260104_140500
# [Dataset] Loaded 1523 samples from run_20260104_140000 (skipped 124 StartSequence)
# [Dataset] Loaded 1687 samples from run_20260104_140300 (skipped 135 StartSequence)
# [Dataset] Loaded 1313 samples from run_20260104_140500 (skipped 98 StartSequence)
# [Dataset] Total samples: 4523
# [Train] Training samples: 3618
# [Train] Validation samples: 905
# [Train] Model parameters: 1,542,434
#
# [Train] Starting training for 50 epochs...
# ================================================================================
# Epoch   1/50 | Train Loss: 0.245617 (T:0.1234, S:0.1222) | Val Loss: 0.198432 (T:0.0987, S:0.0997) [SAVED]
# Epoch   2/50 | Train Loss: 0.156234 (T:0.0782, S:0.0780) | Val Loss: 0.142156 (T:0.0711, S:0.0711) [SAVED]
# ...
# Epoch  50/50 | Train Loss: 0.045123 (T:0.0226, S:0.0225) | Val Loss: 0.052341 (T:0.0262, S:0.0262)
# ================================================================================
# [Train] Training complete!
# [Train] Best validation loss: 0.048912 (epoch 42)
# [Train] Model saved to: experiments/iteration_260104_143052/model.pth
#
# [Train] Generating loss curve...
# [Train] Loss curve saved to: experiments/iteration_260104_143052/logs/loss_curve.png
#
# [Train] Saving training info...
# [Train] Training info saved to: experiments/iteration_260104_143052/training_info.md
# [Train] Training results (JSON) saved to: experiments/iteration_260104_143052/logs/training_results.json
# [Train] Updated training_config.yaml
#
# ================================================================================
# ✅ All training artifacts saved to: experiments/iteration_260104_143052
# ================================================================================
```

**学習時間の目安:**
- RTX 3060 Laptop GPU: 約30-60分（50エポック、4,500フレーム）
- CPU: 約2-4時間

---

### Phase 5: 学習結果の確認

#### A. フォルダ構造

```
experiments/iteration_260104_143052/
├── README.md                      # iteration概要
├── training_config.yaml           # 設定・データソース情報
├── training_config.json           # 同上（JSON形式）
├── model.pth                      # 学習済みモデル ← これを使う！
├── training_info.md               # 詳細な学習結果レポート
├── data_sources/                  # トレーニングデータ（完全コピー）
│   ├── run_20260104_140000/
│   ├── run_20260104_140300/
│   └── run_20260104_140500/
├── evaluation/                    # テスト走行結果（Phase 6で作成）
│   ├── test_run_001.json
│   ├── test_run_002.json
│   ├── test_run_003.json
│   └── evaluation_summary.md
└── logs/                          # 学習ログ
    ├── training_log.txt           # 全エポックのログ
    ├── loss_curve.png             # Loss推移グラフ
    └── training_results.json      # 機械可読な結果
```

#### B. training_info.mdを確認

```bash
# エディタで開く
code experiments/iteration_260104_143052/training_info.md

# または表示
cat experiments/iteration_260104_143052/training_info.md
```

**確認ポイント:**
- ✅ 最良Val Loss < 0.10 が目安
- ✅ Val/Train比 < 1.3 （過学習チェック）
- ✅ Loss曲線が収束しているか

---

### Phase 6: テスト走行（3回）

#### A. モデルをコピー

```bash
# 学習済みmodel.pthをRobot1/models/にコピー
cp experiments/iteration_260104_143052/model.pth models/model.pth
```

#### B. AIモードで3回走行

```bash
# robot_config.txt を編集
# MODE=ai

# 3回走行
.venv/Scripts/python main.py  # 1回目
.venv/Scripts/python main.py  # 2回目
.venv/Scripts/python main.py  # 3回目
```

#### C. 結果を記録（手動）

各走行後、以下を記録:

```json
// experiments/iteration_260104_143052/evaluation/test_run_001.json
{
  "run_number": 1,
  "timestamp": "2026-01-04T15:30:00",
  "completed": false,
  "race_time_sec": 38.2,
  "laps_completed": 0,
  "crash_location": {
    "pos_x": -1.02,
    "pos_y": -0.05,
    "pos_z": 1.85
  },
  "crash_reason": "左コースアウト",
  "notes": "スタート後のコーナーで左に寄りすぎ"
}
```

---

### Phase 7: 評価サマリ作成

```markdown
<!-- experiments/iteration_260104_143052/evaluation/evaluation_summary.md -->
# Evaluation Summary - iteration_260104_143052

## テスト走行結果（3回）

| Run | 完走 | 時間(s) | Lap | クラッシュ地点 | 原因 |
|-----|------|---------|-----|--------------|------|
| 1   | ❌  | 38.2    | 0   | pos_x=-1.02  | 左コースアウト |
| 2   | ✅  | 124.5   | 2   | -            | 2周完走！ |
| 3   | ✅  | 118.9   | 2   | -            | 2周完走！ |

## 統計

- **完走率:** 66.7% (2/3)
- **平均ラップタイム:** 62.3秒（完走run平均）
- **最速ラップ:** 59.4秒

## 観察

### 成功パターン
- Run 2, 3: スムーズなコーナリング
- 左右バランスが改善

### 失敗パターン
- Run 1: 依然として左バイアスが見られる

## 次のアクション

- ✅ 2周完走を初達成！
- ⏳ 完走率を80%以上に向上（追加データ収集）
- ⏳ ラップタイム短縮
```

---

## 🔄 次のIteration

### Iterationを重ねる場合

```bash
# 1. 追加のマニュアル走行（3-5回）
# MODE=keyboard
# → training_data/ に新しいrun_*

# 2. 新しいiteration作成（前回のrunは含めない）
../.venv/Scripts/python scripts/create_iteration.py \
  --data ../training_data \
  --runs run_20260105_100000 run_20260105_100300 run_20260105_100500 \
  --description "Second iteration: focus on right cornering"

# 3. 学習・評価を繰り返し
```

### Iteration間の比較

```bash
# 過去のiterationと比較
ls -l experiments/

# iteration_260104_143052/  ← 初回、完走率66.7%
# iteration_260105_102134/  ← 2回目、完走率？
```

---

## 📊 Colab対応（将来）

### データアップロード

```bash
# 1. iterationフォルダをZIP化
cd experiments
zip -r iteration_260104_143052.zip iteration_260104_143052/data_sources/

# 2. Google Driveにアップロード
```

### Colab Notebook例

```python
# Google Colab
from google.colab import drive
drive.mount('/content/drive')

# データ解凍
!unzip /content/drive/MyDrive/VRR/iteration_260104_143052.zip -d /content/

# コード取得
!git clone https://github.com/YOUR_REPO/virtual-robot-race.git
%cd virtual-robot-race/Project_Beta/Robot1

# 学習実行
!python train_model_extended.py \
  --data /content/iteration_260104_143052/data_sources \
  --output /content/output \
  --epochs 50 \
  --device cuda

# model.pthをDriveに保存
!cp /content/output/model.pth /content/drive/MyDrive/VRR/models/
```

---

## ❓ トラブルシューティング

### Q1: create_iteration.pyで"No valid training data found"

**原因:** データソースディレクトリが間違っている

**解決:**
```bash
# 正しいパス指定
--data ../training_data           # ✅ 正しい（Robot1/から見た相対パス）
--data training_data              # ❌ 間違い
--data /full/path/to/training_data  # ✅ 絶対パスでもOK
```

### Q2: 学習中にCUDA out of memory

**原因:** バッチサイズが大きすぎる

**解決:**
```bash
# バッチサイズを減らす
--batch-size 16  # デフォルト32から減らす
```

### Q3: Loss曲線が表示されない

**原因:** matplotlibのバックエンド問題

**確認:**
```bash
# training_info.mdで確認
# ![Loss Curve](logs/loss_curve.png)

# ファイルが存在するか確認
ls experiments/iteration_*/logs/loss_curve.png
```

---

## 📝 チェックリスト

### Phase 1-2: データ収集
- [ ] 3回マニュアル走行完了
- [ ] analyze_steering_bias.pyでバイアス確認
- [ ] 左右バランスが許容範囲内（±0.05 rad）

### Phase 3: Iteration作成
- [ ] create_iteration.py実行
- [ ] README.mdで内容確認
- [ ] データ統計が正常

### Phase 4: 学習
- [ ] train_model_extended.py実行
- [ ] エラーなく完了
- [ ] Best Val Loss記録

### Phase 5: 結果確認
- [ ] training_info.md確認
- [ ] loss_curve.png確認
- [ ] 過学習チェック（Val/Train < 1.3）

### Phase 6-7: 評価
- [ ] model.pthコピー
- [ ] 3回テスト走行
- [ ] 結果をJSON/MDで記録
- [ ] 完走率を計算

### Phase 8: 次のアクション
- [ ] 改善点を特定
- [ ] 次のiterationの方針決定

---

## 🎯 成功基準

### Iteration成功の定義

| 指標 | 目標 | 備考 |
|------|------|------|
| **完走率** | 80%以上 | 10回中8回完走 |
| **Val Loss** | < 0.08 | MSE Loss |
| **過学習** | Val/Train < 1.3 | 過学習チェック |
| **左右バイアス** | ±0.05 rad以内 | データバランス |

### マイルストーン

- ✅ **Iteration 1:** 初回学習・評価完了
- ⏳ **Iteration 2:** 完走率50%達成
- ⏳ **Iteration 3:** 完走率80%達成
- ⏳ **Iteration 4:** ラップタイム短縮

---

**最終更新:** 2026-01-04
**次回更新:** 初回iteration完了後
