# 6. AIモード：模倣学習とニューラルネットワーク

このレッスンでは、**AIにドライビングを学習させ、自律走行させます。**
難しそうに見えますが、やっていることの本質はシンプルです。
ここでも、AIアシスタント（Gemini Code Assistなど）を積極的に活用しましょう。

**学習目標:**
- 「推論」と「学習」がどこで、どのように行われているかを理解する
- 模倣学習（Imitation Learning）でAIモデルを作る手順を体験する
- ローカルとGoogle Colabの学習コストの違いを体感する
- 強化学習の概念と、このシステムでの位置づけを理解する

> **▶ このレッスンをまず動画で見る**: [Lesson 06 ハンズオン（YouTube）](https://youtu.be/LESSON06_VIDEO_ID)
> 動画にはチャプターが設定されています。各セクションのリンクから該当箇所に直接ジャンプできます。

---

## 1. まずはAIモードで走らせてみよう

`start.bat` を実行してランチャーを開き、以下のように設定します。

| 項目 | 設定値 |
|------|--------|
| **Active** | `1` |
| **R1 mode** | `ai` |

設定を確認したら **START** をクリックします。

### 1.1 サンプルモデルの準備

AIモードには学習済みモデルファイル（`model.pth`）が必要です。
サンプルモデルはリポジトリに含まれており、`git clone` 時点で以下に配置されています。

- `Robot1/models/model.pth`
- `Robot2/models/model.pth`

`Robot1/models/` フォルダを開いて `model.pth` が存在することを確認してください。ファイルがあればそのまま次へ進んでください。

### 1.2 走らせてみる
> **▶ 動画チャプター**: [AIモードで走ってみる](https://youtu.be/LESSON06_VIDEO_ID?t=0)

`start.bat` を起動します。ターミナルに以下のようなログが表示されます：

```
[R1 Inference] Using device: cpu   （またはcuda）
[R1 Inference] Model loaded from ...\Robot1\models\model.pth
[R1 Inference] Waiting for start signal... (Strategy: hybrid)
[R1 Inference] RACE STARTED! (Strategy: hybrid)
[R1 Inference] Drive=+0.523, Steer=-0.031rad(-1.8deg), SOC=1.00
```

> **観察ポイント:**
> - ロボットはどのように走りましたか？
> - `Drive=` と `Steer=` の値は20fps（50ms）ごとに変化しています。
> - モデルの品質によっては、うまく走れないことも正常です。

---

## 2. 推論の仕組み（`inference_input.py`）

`Robot1/inference_input.py` を見てみましょう。AIアシスタントに聞いてみてください：

```
inference_input.py は何をしていますか？
```

---

### 2.1 推論の本体コード

ファイルの中心にあるのは、たった数行のコードです：

```python
# 入力テンソルの準備
image_tensor = _transform(pil_img).unsqueeze(0).to(_device)  # [1, 3, 224, 224]
soc_tensor = torch.tensor([[soc]], dtype=torch.float32).to(_device)  # [1, 1]

# 推論の実行
with torch.no_grad():
    output = _model(image_tensor, soc_tensor)
    raw_drive = output[0, 0].item()   # drive_torque
    raw_steer = output[0, 1].item()   # steer_angle
```

**これがすべてです。** 2つのデータを入力し、2つのデータが返ってくる。これがMIMOです。

---

### 2.2 モデルの構造（`model.py`）

ニューラルネットワーク（`DrivingNetwork`）の構造はシンプルです：

```
入力①: RGB画像 224×224      → CNN（畳み込み4段 + GlobalAvgPool）→ 256次元ベクトル
                                                                      ↓ 結合（concat）
入力②: SOC（浮動小数点1個） ─────────────────────────────────────→ 257次元ベクトル
                                                                      ↓ MLP（全結合）
出力: [drive_torque, steer_angle]（2次元）
```

> **補足**: CNN（Convolutional Neural Network）は画像から特徴を抽出します。
> 「コースが右にカーブしている」「白線が左に寄っている」などの視覚情報を数値化します。

---

### 2.3 Hybridモード vs Pure E2Eモード

このシステムには2つのモードがあります（`ai_control_strategy.py` で設定）：

| モード | スタート検出 | 走行制御 | 特徴 |
|--------|------------|---------|------|
| **hybrid** (デフォルト) | ルールベース | AI | スタート合図の検出は確実なルールで処理 |
| **pure_e2e** | AI | AI | 完全にAIに任せる（スタート合図も学習対象） |

> ルールで確実に処理できることをわざわざAIに学習させる必要はありません。
> 「決まり切った処理はルール、判断が難しい処理はAI」が現実的なアプローチです。

---

## 3. AIモデルを学習させる

### 3.1 「模倣学習」とは何か？

このシステムが使っている学習手法は**模倣学習（Imitation Learning）**です。

1. 人間（あなた）がキーボードで走る
2. そのときの「画像・SOC → アクセル・ハンドル」というデータを記録
3. AIは「人間ならこの画像でこう動く」というパターンを学習する

つまり、**AIは「あなたの運転を真似る」** ように学習します。
うまく走れるAIを作りたければ、うまく走ったデータを与えることが重要です。

> **重要**: この学習はレース中にリアルタイムで行われるのではありません。
> 走行データを収集 → **オフラインで学習** → 学習済みモデルで走行、という流れです。

---

### 3.2 学習関連ファイルの構造

```
Robot1/
├── model.py                     ← ニューラルネットワーク定義（変更しない）
├── models/
│   └── model.pth                ← 使用する学習済みモデル（ここに置く）
│
├── training_data/               ← キーボード走行で収集したデータ（DATA_SAVE=1で保存）
│   ├── run_20260216_094415/
│   │   ├── images/
│   │   └── metadata.csv
│   └── run_.../
│
├── ai_training/                 ← 学習スクリプト群
│   ├── train.py                 ← メインの学習スクリプト
│   ├── run_pipeline.py          ← 反復学習パイプライン管理
│   ├── run_scorer.py            ← 走行データの品質スコアリング
│   ├── run_iteration.py         ← 1イテレーション実行
│   ├── create_iteration.py      ← イテレーションフォルダ作成
│   └── analyze.py               ← データ分析ツール
│
└── experiments/                 ← 学習結果の保存先（.gitignoreで除外）
    └── iteration_[timestamp]/   ← 1回の学習試行
        ├── data_sources/        ← 学習に使ったデータのコピー
        ├── model.pth            ← この試行で作ったモデル
        ├── model_best.pth       ← 検証lossが最小だったモデル
        ├── training_log.csv     ← エポックごとのloss推移
        └── dataset_manifest.json← 使用データセットの統計情報
```

---

### 3.3 ローカルでの学習手順
> **▶ 動画チャプター**: [データ収集と学習の実行](https://youtu.be/LESSON06_VIDEO_ID?t=0)

**Step 1: データを収集する**

`start.bat` を実行してランチャーを開き、以下の設定でキーボードモードで走行します。

| 項目 | 設定値 |
|------|--------|
| **Active** | `1` |
| **R1 mode** | `keyboard` |
| **Data save** | `ON` |

走行が終わると `Robot1/training_data/run_[日付時刻]/` フォルダが作成されます。
最低でも3回分のデータがあると学習の効果が出やすいです。

**Step 2: 学習を実行する**

`Robot1/` ディレクトリで以下のコマンドを実行します：

```bash
python ai_training/train.py --data training_data
```

学習が始まると、エポックごとにlossが表示されます：

```
Epoch   1/100 | Train: 0.045312 | Val: 0.048201 | LR: 1.00e-04 | 12.3s
Epoch   2/100 | Train: 0.038441 | Val: 0.041023 | LR: 1.00e-04 | 12.1s ✓ NEW BEST
...
⏹️  Early stopping triggered at epoch 47
Best validation loss: 0.012345
Model saved to: experiments/iteration_[timestamp]/model.pth
```

**Step 3: モデルを配置する**

生成されたモデルを `models/` フォルダにコピーします。`[timestamp]` の部分は、実際のフォルダ名に置き換えてください。

```bash
cp experiments/iteration_[timestamp]/model_best.pth models/model.pth
```

> **ポイント**: `model.pth` (最終エポックのモデル) よりも `model_best.pth` (検証ロスが最小だったモデル) を使う方が、性能が良い傾向にあります。

**Step 4: AIモードで走らせる**

ランチャーで **R1 mode=`ai`** に設定して **START** します。

---

### 3.4 学習データのフィルタリング

`train.py` は `metadata.csv` の `status` カラムを使って学習データをフィルタリングします：

| 使用する | 除外する |
|----------|----------|
| `Lap0`, `Lap1`, `Lap2`, `Finish` | `StartSequence`, `Fallen`, `FalseStart`, `ForceEnd` |

スタート待ち中や落下後のデータは「正しいドライビング」ではないため除外されます。

---

## 4. Google Colabで学習する
> **▶ 動画チャプター**: [Google Colabで学習する](https://youtu.be/LESSON06_VIDEO_ID?t=0)

### 4.1 なぜColabを使うのか？

ローカルPCにGPUがない場合、学習に非常に時間がかかります（数十分〜数時間）。
Google ColabのGPUを使うと、**同じデータでも数分〜10分程度**で学習が完了します。

> **体感してほしいこと**: ローカルで1時間かかっていた学習が、Colabでは5分で終わることがあります。これが「GPUの力」です。AIモデルの開発では「どれだけ速く試行錯誤できるか」が重要で、学習が速いほど改善サイクルを多く回せます。クラウドGPUを使うことの価値を、数字で体感してください。

これを**「学習コスト」**と呼びます。GPUの性能差と、クラウドに課金する意味を体感してください。

---

### 4.2 Colabでの学習手順

`colab/train_on_colab.ipynb` がその手順書です。以下の流れで実行します：

**1. Google Driveに準備するファイル**

以下を Google Drive の `/MyDrive/virtual-robot-race/` にアップロードします：

| ファイル/フォルダ | Driveのパス |
|----------------|------------|
| `Robot1/training_data/` | `/MyDrive/virtual-robot-race/training_data/` |
| `Robot1/model.py` | `/MyDrive/virtual-robot-race/model.py` |

**2. Colabでの設定**

- ランタイム → ランタイムのタイプを変更 → **GPU** を選択（T4で十分です）

**3. セルを順番に実行する**

| セル | 内容 |
|------|------|
| Cell 1 | Google Driveをマウント・パス設定 |
| Cell 2 | PyTorch・CUDAの確認 |
| Cell 3 | イテレーションフォルダ作成 |
| Cell 4 | `training_data/` の run_ を `data_sources/` へ自動コピー |
| Cell 5 | dataset_manifest.json の生成（サンプル数・完走判定など） |
| Cell 6 | モデル初期化・DataLoader作成・Data Augmentation設定 |
| Cell 7 | 学習ループ（最大100エポック、Early stopping付き） |
| Cell 8 | 学習曲線グラフの生成・サマリー表示 |

**4. model.pthをダウンロードする**

学習完了後、`iteration_[timestamp]/model.pth` をダウンロードします。
ローカルの `Robot1/models/model.pth` に上書き保存して完了です。

---

## 5. バッチ学習とリアルタイム学習の違い

> **重要**: このシステムの模倣学習は**バッチ学習（オフライン学習）**です。

```
バッチ学習（模倣学習）:
  キーボード走行 → データ収集 → オフラインで学習 → モデル配置 → 走行テスト → 繰り返し

リアルタイム強化学習:
  走行しながら → 報酬を計算 → その場でモデルを更新 → 走り続ける
```

MIMOの構成（画像+SOC → トルク+ステア）では、**位置情報（pos_x, pos_z）がリアルタイムに取得できません**。`metadata.csv` はレース終了時にのみ届くためです。このため、位置情報を使った高度な報酬設計を必要とするリアルタイム強化学習には制約があります。

---

## 6. より高度な学習：DAggerと報酬設計

### 6.1 模倣学習の限界

最初に学習したモデルには弱点があります。**人間が走ったことのない場面**に遭遇すると、正しく対処できません。

例えば：
- 少しコースをはみ出した場面 → 人間のデータにないので、回復方法を知らない
- ラップを重ねるごとに少しずつズレていく → 最初だけうまくても崩れる

これを「**分布シフト（Distribution Shift）**」と呼びます。

---

### 6.2 DAgger：反復的なデータ収集で改善する
> **▶ 動画チャプター**: [DAgger反復改善サイクル](https://youtu.be/LESSON06_VIDEO_ID?t=0)

この問題を解決する手法が **DAgger（Dataset Aggregation）**です。
`run_pipeline.py` がこのパイプラインを実装しています。

```
DAggerのサイクル:

  1. 人間のデータで最初のモデルを学習
         ↓
  2. そのモデルをAIモードで走行させる（ロールアウト）
         ↓
  3. AIが走ったデータを「人間のデータに追加」する
         ↓
  4. 統合データで再学習（学習データが増えるほど強くなる）
         ↓
  2に戻る（繰り返し）
```

AIが自分では経験しなかった場面をどんどん学習データに取り込むことで、
徐々に「どんな状況でも対処できる」AIになっていきます。

**使い方:**

```bash
# パイプラインの現在の状態を確認
python ai_training/run_pipeline.py status

# 次のステップ（学習 or ロールアウト）を実行
python ai_training/run_pipeline.py next
```

> **💡 自分でコードを書く必要はありません**: `run_pipeline.py next` を実行するだけで、「学習 → AIで走行 → データ追加 → 再学習」のサイクルを自動で管理してくれます。「DAggerって自分でゼロから実装するの？」という心配は不要です。

---

### 6.3 報酬設計：データの「質」を数値化する

DAggerで集めたデータをすべて均等に使うのではなく、
**「良い走り」のデータを重く、「悪い走り」のデータを軽く（または除外）** 使う仕組みがあります。

これを担うのが `rl_reward.py` と `run_scorer.py` です。

| ファイル | 役割 |
|---------|------|
| `rl_reward.py` | 走行の「良さ」の評価基準（報酬の重み）を定義 |
| `run_scorer.py` | `metadata.csv` を分析して各runにスコアをつける |
| `train.py` | スコアに基づいてデータを選別・重み付けして学習に使う |

> **注意**: `rl_reward.py` は**リアルタイムでモデルを更新するためではありません**。
> レース終了後に `metadata.csv` を読んで走行品質をスコアリングするための「採点基準」です。
> 現バージョンでは、位置情報（pos_x, pos_z）はリアルタイムに取得できないため、
> 走行中にリアルタイムで強化学習を行うことは実用的ではありません。

> **よくある誤解**: 「タイムのスコアを厳しくすれば、AIが勝手に速く走るようになるの？」
> → **なりません。** スコアは「どのデータを学習に使うかの選別基準」です。AIの強化学習（試行錯誤しながら自動で上手くなる）とは異なります。このシステムでは「**良い走りをした人間のデータを選別して学習させる**」という模倣学習が基本です。AIが速くなるには、速く走れた人間のデータが必要です。

---

### 6.4 報酬の中身

`rl_reward.py` と `run_scorer.py` には現在以下の評価基準が実装されています：

| 評価項目 | 内容 |
|---------|------|
| 完走ボーナス | 2周完走（+1000）、1周完走（+400）|
| タイム | 速いほど高スコア（基準120秒、1秒ごとに-2）|
| SOC効率 | バッテリーを残して完走するほど高スコア |
| 操作の滑らかさ | ハンドルのジャークが少ないほど高スコア |
| ペナルティ | 落下（-500）、強制終了（-100）|

この「採点基準」を書き換えることで、どんな走りを「良い走り」と定義するかを変えられます。

AIアシスタントと以下を議論してみましょう：

```
run_scorer.py と rl_reward.py の採点基準を見てください。
「2周を最短タイムで完走する」という目標に対して、
より効果的なスコアリングのアイデアはありますか？
```

---

## 7. レッスン課題

### 課題1: キーボードデータから自分のAIモデルを作る（ローカル）

1. ランチャーで **R1 mode=`keyboard`、Data save=`ON`** に設定してキーボード走行を3回行う
2. `ai_training/train.py` でローカル学習を実行する
3. 生成された `model.pth` を `models/` に配置し、ランチャーで **R1 mode=`ai`** に設定してAIモードで走行を確認する
4. 学習にかかった時間を記録する（**学習コスト①**）

### 課題2: 同じデータをColabで学習する

1. 課題1と同じ `training_data/` を Google Drive にアップロードする
2. `colab/train_on_colab.ipynb` を使って学習を実行する
3. 学習にかかった時間を記録する（**学習コスト②**）

> **考えてみよう:**
> - ローカルとColabで学習時間はどれくらい違いましたか？
> - GPUのスペックや、クラウドに課金することの意味を感じましたか？
> - 3回分のデータから作ったAIは、どれくらいうまく走れましたか？

### 課題3: AIと対話して「さらに強くする」方法を議論する

以下をAIアシスタントに相談してみましょう：

```
現在のモデルの走りを見て、改善するためのアイデアを提案してください。
以下の観点から議論したいです：
- データをどう増やすか・質を上げるか（うまく走った周回だけ使うなど）
- モデルの構造（model.py）を変えると何が変わるか
- ハイブリッドモードとPure E2Eの使い分けは？
- DAgger（データ収集→学習→AIロールアウト→データ追加→再学習）を使うとどう変わるか
- run_scorer.py の採点基準を変えると学習データの選別がどう変わるか
```

---

### 関連資料
- [05_Rule_Based_Control.md](05_Rule_Based_Control.md)
- [04_Log_and_Table_Mode.md](04_Log_and_Table_Mode.md)
- [用語集](99_Glossary.md)

---

> **❓ うまくいかない場合は？**
> [NotebookLM](https://notebooklm.google.com/notebook/ab916e69-f78b-47c3-9982-a5210a07d713) にエラーメッセージをそのまま貼り付けて質問してください。

---

⬅️ [前のレッスン: 05_Rule_Based_Control.md（ルールベース制御）](05_Rule_Based_Control.md) ｜ ➡️ [次のレッスン: 07_How_to_Join_Race.md（レース参加方法）](07_How_to_Join_Race.md)
