# VRR Beta 1.4: BCからオフライン強化学習への道

このドキュメントは、Virtual Robot Race (VRR) プロジェクトにおける
模倣学習から強化学習への発展過程を記録したものです。

---

## 1. 学習パラダイムの全体像

```
教師あり学習
    │
    ▼
模倣学習 (Imitation Learning)
    ├─ BC (Behavioral Cloning)        ← Phase 0
    ├─ DAgger                         ← Phase 0.5
    └─ RW-BC (Reward-Weighted BC)     ← Phase 1 ✓完了
    │
    ▼
オフライン強化学習 (Offline RL)
    ├─ RW-BC + 累積報酬              ← Phase 2
    └─ AWR (Advantage-Weighted)       ← Phase 3
```

---

## 2. 各Phase の詳細

### Phase 0: BC (Behavioral Cloning)

**考え方**: 先生（人間）の操作をそのままコピーする

**アルゴリズム**:
```
入力: カメラ画像 + SOC
出力: drive_torque, steer_angle

損失 = MSE(予測, 先生の操作)
     = Σ (予測 - 正解)²
       全フレーム均等
```

**特徴**:
- シンプルで実装が簡単
- 先生のデータ品質に依存
- 分布シフト問題: AIが少しずれると未知の状態に遭遇し、さらにずれる

**VRRでの結果**: 落下することがある

---

### Phase 0.5: DAgger (Dataset Aggregation)

**考え方**: AIが走行 → 失敗しそうな場所で先生が介入 → データ追加 → 再学習

**アルゴリズム**:
```
1. 初期データで BC学習 → モデル v1
2. モデル v1 で走行 → 新データ収集（先生が介入）
3. 全データで再学習 → モデル v2
4. 繰り返し...
```

**特徴**:
- 分布シフト問題を軽減
- AIが遭遇する状態をカバー
- 人間の介入が必要

**VRRでの実装**: DAgger iteration システム

---

### Phase 1: RW-BC (Reward-Weighted Behavioral Cloning) ✓完了

**考え方**: 良いデータを重視して学習する

**アルゴリズム**:
```
重み = exp(報酬 / temperature)

損失 = Σ 重み × (予測 - 正解)²
       ↑
       高スコアのフレームほど重みが大きい
```

**Temperature の効果**:
| 値 | 効果 |
|----|------|
| 0.5 (低) | 高報酬フレームを強く重視 |
| 1.0 (中) | バランス |
| 2.0 (高) | ほぼ均等（BCに近い）|

**VRRでの実装**:
```bash
# 通常BC
python train.py --data training_data --mode bc

# Reward-Weighted BC
python train.py --data training_data --mode rw --temperature 1.0

# スコアフィルタリング + RW-BC
python train.py --data training_data --mode rw --min-score 1000
```

**実験結果**:
| 手法 | 結果 |
|------|------|
| BC (重みなし) | 落下 |
| RW-BC (temp=1.0) | 2周完走 |
| RW-BC (temp=0.5) | 2周完走（より速い）|

---

### Phase 2: フレームレベル報酬の詳細化（次のステップ）

**考え方**: metadata.csv の位置情報を活用して、フレームごとに異なる報酬を計算

**Phase 1 との違い**:
```
Phase 1:
  フレーム報酬 = runスコア / フレーム数 + 終了ボーナス
               ↑
               全フレームほぼ同じ値

Phase 2:
  フレーム報酬 = 生存 + SOC効率 + 進行度 + ラップボーナス + ...
               ↑
               フレームごとに異なる報酬
               「このカーブをうまく曲がった」が高報酬
               「落下直前の悪い操作」が低報酬
```

**報酬の要素**:
| 要素 | 計算方法 | 報酬例 |
|------|---------|--------|
| 生存 | 毎フレーム | +0.1 |
| SOC効率 | SOC変化量 | +0.5 × ΔSOC |
| 進行度 | 位置から計算 | +1.0 × 進行距離 |
| ラップ完了 | status変化 | +50 (Lap1), +100 (Finish) |
| 落下 | status=Fallen | -100 |
| 滑らかさ | ステア変化量 | -0.1 × |Δsteer| |

**累積報酬（将来の報酬を考慮）**:
```
R_t = r_t + γ × r_{t+1} + γ² × r_{t+2} + ...

γ = 0.99 (割引率)

意味: 今の行動が将来にどう影響するかを考慮
      ゴール直前のフレームより、序盤の重要な判断を重視
```

---

### Phase 3: AWR (Advantage-Weighted Regression)

**考え方**: 「平均より良かったか？」で重み付け

**Phase 2 との違い**:
```
Phase 2:
  重み = exp(累積報酬 / temp)
  問題: 良いrunの全フレームが高重み

Phase 3:
  重み = exp(アドバンテージ / temp)
  アドバンテージ = 累積報酬 - 期待報酬
                            ↑
                            価値関数 V(状態) が予測
```

**アドバンテージの意味**:
```
例: あるカーブでの3つの走行データ

  走行A: 累積報酬 = 100, 期待報酬 = 110 → アドバンテージ = -10 (平均以下)
  走行B: 累積報酬 = 150, 期待報酬 = 110 → アドバンテージ = +40 (平均以上)
  走行C: 累積報酬 = 80,  期待報酬 = 110 → アドバンテージ = -30 (平均以下)

  → 走行B の操作を重視して学習
```

**実装の追加要素**:
- 価値関数ネットワーク V(画像, SOC) → 期待累積報酬
- 2段階学習: (1) 価値関数を学習 (2) ポリシーを重み付き学習

---

## 3. 報酬設計の哲学

### 報酬設計は「あなたが決めるもの」

```
自動では決まりません。

「速く走る」「安全に走る」「電池を節約する」
どれを重視するかは設計者の意図次第です。
```

### 段階的な報酬設計

```
Step 1: 完走を安定させる
        報酬 = 完走ボーナス(大) + タイム(小)
        目標: 完走率 90%以上

Step 2: タイムを追求
        報酬 = 完走(前提) + タイム(重視)
        目標: 安定した速いタイム

Step 3: 人間を超える
        報酬 = 人間ベストタイム基準
        目標: 人間より速く走る
```

### 報酬設計の例

**完走重視（Phase 1）**:
```python
reward = 0
if status == "Finish":
    reward += 1000
elif status == "Lap1":
    reward += 300
elif status == "Fallen":
    reward -= 200
reward += final_soc * 50
```

**タイム重視（Phase 2以降）**:
```python
if status != "Finish":
    return -500

human_best = 35.0  # 秒
reward = (human_best - ai_time) * 100
# 30秒 → +500点（人間超え）
# 35秒 → 0点（人間と同等）
# 40秒 → -500点（人間より遅い）
```

---

## 4. BCからオフラインRLへ：なぜ強化学習か？

### BCの限界

```
BC: 「先生がやったことをコピー」

限界: 先生が35秒なら、AIも35秒が限界
      先生を超えることはできない
```

### オフラインRLの強み

```
オフラインRL: 「良い行動を強化、悪い行動を弱化」

強み:
  - 先生の良い部分だけを抽出
  - 複数の走行データの良いところを組み合わせ
  - 報酬設計次第で先生を超えられる
```

### VRRでオフラインRLが適している理由

```
Unity実行中:
  ├─ カメラ画像 ✓
  ├─ SOC ✓
  ├─ 位置・向き ✗ (リアルタイム取得不可)
  └─ 報酬 ✗ (リアルタイム計算不可)

走行後 (metadata.csv):
  ├─ pos_x, pos_z ✓
  ├─ rotation_y ✓
  ├─ status ✓
  └─ 報酬を後から計算可能 ✓

→ オンラインRLは難しいが、オフラインRLは可能
```

---

## 5. 実装ファイル構成

```
Robot1/
├── ai_training/
│   ├── train.py          # メイン学習スクリプト
│   │                       --mode bc|rw
│   │                       --temperature FLOAT
│   │                       --finetune PATH
│   │                       --min-score FLOAT
│   │                       --top-percent FLOAT
│   │
│   ├── run_scorer.py     # ラン評価スクリプト
│   │                       完走、タイム、SOC、滑らかさでスコア計算
│   │
│   └── config.yaml       # 学習設定
│
├── models/
│   └── model.pth         # 現在の最良モデル
│
└── experiments/
    └── iteration_XXXXXX/ # 各学習イテレーション
        ├── model.pth
        ├── training_log.csv
        └── data_sources/
```

---

## 6. 今後の実装計画

### Phase 2 実装タスク

1. **フレームレベル報酬計算の改良**
   - metadata.csv から位置情報を読み込み
   - 進行度（トラック上の位置）を計算
   - フレームごとの詳細な報酬を計算

2. **累積報酬の計算**
   - 割引率 γ を導入
   - 各フレームの累積将来報酬を計算

3. **train.py の拡張**
   - `--reward-type simple|detailed` オプション追加

### Phase 3 実装タスク

1. **価値関数ネットワークの追加**
   - DrivingNetwork と同様の構造
   - 出力: スカラー値（期待累積報酬）

2. **2段階学習の実装**
   - Stage 1: 価値関数を学習
   - Stage 2: アドバンテージでポリシーを学習

3. **train.py の拡張**
   - `--mode awr` オプション追加

---

## 7. 実験結果サマリー（2026-01-17）

### 各手法の比較

| Phase | 手法 | Best Val Loss | 走行結果 | 特徴 |
|-------|------|---------------|----------|------|
| 0 | BC | - | 落下 | シンプルだが分布シフトに弱い |
| 1 | RW-BC (temp=1.0) | 0.0316 | 2周完走 | 安定 |
| 1 | RW-BC (temp=0.5) | 0.0309 | 2周完走 | より速い |
| 2 | RW-BC + 詳細報酬 | - | 落下 | 落下データも含めると不安定 |
| 2 | RW-BC + 詳細報酬 + min-score | ~0.030 | 2周完走 | 完走データのみで安定 |
| 3 | AWR | 0.0308 | 2周完走（ギリギリ） | 速いがアグレッシブすぎる |

### 重要な発見

1. **データ品質が最重要**
   - 落下データを含めると悪い操作パターンを学習
   - `--min-score 1000` で完走データのみ使用すると安定

2. **Phase 2 (RW-BC + 詳細報酬 + min-score) が現時点でベスト**
   - 安定性と速さのバランスが良い
   - 推奨コマンド:
   ```bash
   python train.py --data training_data --mode rw --reward-type detailed --min-score 1000
   ```

3. **AWR は速いがチューニングが必要**
   - 壁にぶつかりやすい
   - 報酬設計（smoothness_penalty増加など）で改善の余地あり

---

## 8. 今後の方針

### 優先度1: データソースの強化（最重要）

```
現状:
  完走データ: 5-6 runs
  落下データ: 5-6 runs

目標:
  完走データ: 20+ runs
  多様な走行パターン
```

**データ収集の戦略:**

| ソース | 期待される特徴 |
|--------|----------------|
| マニュアル（人間） | 多様な判断、リカバリー能力 |
| ルールベース | 安定した基本動作 |
| 現行AI（RW-BC） | 既存の良いパターンの再現 |

### 優先度2: 既存手法の改善

**AWR の報酬設計調整:**
```python
# 現在
REWARD_CONFIG = {
    'smoothness_penalty': 0.5,
    'progress_reward': 1.0,
}

# 提案（安定性重視）
REWARD_CONFIG = {
    'smoothness_penalty': 1.0,   # 増加
    'progress_reward': 0.5,      # 減少
    'wall_penalty': -1.0,        # 新規追加（位置情報から）
}
```

### 優先度3: 新しい手法の検討

**候補:**
- IQL (Implicit Q-Learning): より高度なオフラインRL
- Decision Transformer: Transformerベースのアプローチ
- CQL (Conservative Q-Learning): 保守的なQ学習

---

## 9. 実装済みCLIオプション一覧

```bash
# 基本
python train.py --data training_data

# Phase 1: RW-BC
python train.py --data training_data --mode rw --temperature 1.0

# Phase 2: 詳細報酬
python train.py --data training_data --mode rw --reward-type detailed

# Phase 2 + スコアフィルタリング（推奨）
python train.py --data training_data --mode rw --reward-type detailed --min-score 1000

# Phase 3: AWR
python train.py --data training_data --mode awr --reward-type detailed --min-score 1000

# ファインチューニング
python train.py --data training_data --mode rw --finetune models/model.pth

# 温度調整
python train.py --data training_data --mode rw --temperature 0.5
```

---

## 10. 参考文献

- **Behavioral Cloning**: Pomerleau (1991) "ALVINN: An Autonomous Land Vehicle in a Neural Network"
- **DAgger**: Ross et al. (2011) "A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning"
- **AWR**: Peng et al. (2019) "Advantage-Weighted Regression: Simple and Scalable Off-Policy Reinforcement Learning"
- **Offline RL Survey**: Levine et al. (2020) "Offline Reinforcement Learning: Tutorial, Review, and Perspectives on Open Problems"
- **IQL**: Kostrikov et al. (2022) "Offline Reinforcement Learning with Implicit Q-Learning"

---

## 更新履歴

| 日付 | 内容 |
|------|------|
| 2026-01-12 | Phase 1 (RW-BC) 実装完了、実験成功 |
| 2026-01-17 | Phase 2 (詳細報酬) 実装完了 |
| 2026-01-17 | Phase 3 (AWR) 実装完了 |
| 2026-01-17 | 実験結果サマリーと今後の方針を追加 |
