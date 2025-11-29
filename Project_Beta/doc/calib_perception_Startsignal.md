# calib_perception_Startsignal.py

## 概要

スタートシグナル検出（`perception_Startsignal.py`）のキャリブレーション・調整用ツール。

閾値パラメータの調整、検出結果の可視化、バッチ処理によるシーケンス検証を行う。

## ファイル位置

```
Project_Beta/Robot1/rule_based_algorithms/calib_perception_Startsignal.py
```

## フォルダ構造

```
Robot1/debug/
├── input_jpg/    # 検証用の入力画像を置く
└── output/       # 結果（オーバーレイ画像 + CSV）を出力
    ├── frame_000001.jpg   # オーバーレイ画像（入力と同名）
    ├── frame_000002.jpg
    └── results.csv        # 検出結果CSV
```

## 使用方法

### 基本（デフォルトフォルダ）

```bash
cd Project_Beta/Robot1/rule_based_algorithms

# input_jpg/ に画像を置いて実行
python calib_perception_Startsignal.py
```

### 単一画像

```bash
python calib_perception_Startsignal.py --image debug/input_jpg/sample.jpg
```

### カスタム閾値でテスト

```bash
python calib_perception_Startsignal.py --red_thresh 150 --ratio_thresh 0.05
```

### 閾値スイープ（最適値探索）

```bash
python calib_perception_Startsignal.py --sweep_thresh --image debug/input_jpg/sample.jpg
```

### ヘルプ

```bash
python calib_perception_Startsignal.py --help
```

## コマンドライン引数

| 引数 | デフォルト | 説明 |
|------|-----------|------|
| `--image` | - | 単一画像のパス |
| `--folder` | `debug/input_jpg/` | 画像フォルダのパス |
| `--out_dir` | `debug/output/` | 出力ディレクトリ |
| `--no_overlay` | False | オーバーレイ画像を保存しない |
| `--sweep_thresh` | False | 閾値スイープモード |
| `--red_thresh` | 140 | 赤チャンネル閾値 |
| `--green_thresh` | 130 | 緑チャンネル閾値 |
| `--blue_thresh` | 130 | 青チャンネル閾値 |
| `--ratio_thresh` | 0.03 | 点灯判定の比率閾値（3%） |

## 出力ファイル

### オーバーレイ画像

入力画像に以下を描画：

1. **ランプROI枠線**（画像上部）
   - 緑枠: 点灯検出
   - 赤枠: 消灯検出

2. **情報パネル**（画像中央〜下部、半透明白背景）
   - 各ランプの赤ピクセル比率とON/OFF状態
   - Red Count（点灯数）
   - Ready状態
   - GO状態
   - 使用した閾値パラメータ

### results.csv

| カラム | 説明 |
|--------|------|
| `filename` | ファイル名 |
| `red_count` | 点灯ランプ数（0〜3） |
| `ready_to_go` | 3灯点灯後のready状態 |
| `is_go` | GOタイミング検出 |
| `lamp1_ratio` | ランプ1の赤ピクセル比率 |
| `lamp1_on` | ランプ1の点灯状態 |
| `lamp2_ratio` | ランプ2の赤ピクセル比率 |
| `lamp2_on` | ランプ2の点灯状態 |
| `lamp3_ratio` | ランプ3の赤ピクセル比率 |
| `lamp3_on` | ランプ3の点灯状態 |

### threshold_sweep.csv（--sweep_thresh時）

閾値の組み合わせごとの検出結果を出力。最適な閾値を探索するために使用。

## 主要関数

### `analyze_startsignal(img, **thresh_kwargs) -> SignalResult`

画像を解析し、各ランプの状態と全体のGO判定を返す。

### `draw_overlay(img, result, **thresh_kwargs) -> Image`

検出結果をオーバーレイした画像を生成。

### `process_single(image_path, ...) -> SignalResult`

単一画像を処理。

### `process_batch(folder, ...) -> List[Tuple[str, SignalResult]]`

フォルダ内の画像をバッチ処理。シーケンス追跡（ready_to_go状態の引き継ぎ）に対応。

### `sweep_threshold(image_path, ...) -> None`

閾値をスイープして最適値を探索。

## 検出ロジック

### ランプ領域（ROI）

```python
# 画像上部20%の領域
top = 0
bottom = int(height * 0.2)

# 3つのランプ位置（横方向）
lamp_positions = [
    (int(width * 0.35), int(width * 0.50)),  # ランプ1
    (int(width * 0.55), int(width * 0.70)),  # ランプ2
    (int(width * 0.75), int(width * 0.90)),  # ランプ3
]
```

### 赤色判定

```python
def is_red(pixel, red_thresh=140, green_thresh=130, blue_thresh=130):
    r, g, b = pixel[:3]
    return r > red_thresh and g < green_thresh and b < blue_thresh
```

### 点灯判定

```python
ratio = red_pixels / total_pixels
is_on = ratio > ratio_thresh  # デフォルト: 3%
```

### GO判定ロジック

```
[初期状態] ready_to_go = False
    ↓ 3灯すべて点灯（red_count == 3）
[待機状態] ready_to_go = True
    ↓ 3灯すべて消灯（red_count == 0）
[GO発火] is_go = True（一度だけ）
```

## 調整可能なパラメータ

### 描画位置

[calib_perception_Startsignal.py:182](../Robot1/rule_based_algorithms/calib_perception_Startsignal.py#L182)

```python
panel_top = int(height * 0.45)  # 画像の45%位置から開始
```

### 背景透明度

[calib_perception_Startsignal.py:214](../Robot1/rule_based_algorithms/calib_perception_Startsignal.py#L214)

```python
fill=(255, 255, 255, 160)  # 半透明の白（160/255 ≈ 63%不透明）
```

## 使用例：シーケンス検証

```
入力画像（時系列順）:
  frame_000001.jpg  → 1灯点灯
  frame_000019.jpg  → 2灯点灯
  frame_000032.jpg  → 3灯点灯（ready!）
  frame_000089.jpg  → 全消灯（GO!）

出力CSV:
  filename,red_count,ready_to_go,is_go,...
  frame_000001.jpg,1,False,False,...
  frame_000019.jpg,2,False,False,...
  frame_000032.jpg,3,True,False,...   ← ready!
  frame_000089.jpg,0,False,True,...   ← GO!
```

## 関連ファイル

- [perception_Startsignal.py](../Robot1/rule_based_algorithms/perception_Startsignal.py) - 本体（実際のレースで使用）
- [perception_Startsignal.md](./perception_Startsignal.md) - 本体のドキュメント
- [rule_based_input.py](../Robot1/rule_based_input.py) - 本体を呼び出すモジュール
