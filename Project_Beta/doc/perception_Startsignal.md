# perception_Startsignal.py

## 概要

レース開始シグナル（3連赤ランプ）を検出し、GOタイミングを判定するモジュール。

F1のスタートシグナルと同様に、3つの赤ランプが全点灯した後、全消灯したタイミングで「GO」を返す。

## ファイル位置

```
Project_Beta/Robot1/rule_based_algorithms/perception_Startsignal.py
```

## 制御フロー内での役割

```
rule_based_input.py update() @20Hz
    │
    ├─ [START待ち] ← ここで使用
    │      perception_Startsignal.detect_start_signal(pil_img)
    │      └─ True が返ったら _started_latch = True → 走行開始
    │
    └─ [走行中] sliding_windows → driver_model
```

## 制御方針

### 状態遷移

```
[初期状態]
    ready_to_go = False
        │
        ▼ 3灯すべて点灯を検出
[待機状態]
    ready_to_go = True
        │
        ▼ 3灯すべて消灯を検出
[GO発火]
    return True (一度だけ)
    ready_to_go = False にリセット
```

### 検出ロジック

1. **ROI設定**: 画像上部20%（`height * 0.0 ~ 0.2`）
2. **ランプ領域定義**: 3つの矩形領域
   - ランプ1: `width * 0.35 ~ 0.50`
   - ランプ2: `width * 0.55 ~ 0.70`
   - ランプ3: `width * 0.75 ~ 0.90`
3. **赤判定**: 各領域内の赤ピクセル比率 > 3% なら「点灯」
4. **GO判定**: 3灯点灯後 → 3灯消灯で `True` を返す

## 使用技術

### 赤色判定（RGB閾値）

```python
def is_red(pixel, red_thresh=140, green_thresh=130, blue_thresh=130):
    r, g, b = pixel
    return r > red_thresh and g < green_thresh and b < blue_thresh
```

- **R > 140**: 赤チャンネルが十分に高い
- **G < 130, B < 130**: 緑・青チャンネルが低い（純粋な赤に近い）

### 状態ラッチ（関数属性）

```python
if not hasattr(detect_start_signal, 'ready_to_go'):
    detect_start_signal.ready_to_go = False
```

Pythonの関数属性を使って状態を保持。モジュールレベルのグローバル変数を避けつつ、呼び出し間で状態を維持。

## API

### `detect_start_signal(img: PIL.Image) -> bool`

| 引数 | 型 | 説明 |
|------|-----|------|
| `img` | PIL.Image | RGB形式のカメラ画像 |

| 戻り値 | 説明 |
|--------|------|
| `True` | GO! (3灯点灯後の消灯を検出、一度だけ) |
| `False` | まだGOではない、またはすでにGO済み |

## デバッグモード

`DEBUG_MODE = True` に設定すると、ランプ検出領域を赤枠で描画した画像を `debug_lamps.jpg` として保存。

```python
DEBUG_MODE = False  # 本番では False
if DEBUG_MODE:
    from PIL import ImageDraw
    # ... 検出領域を描画して保存
```

## 注意事項

- GOは**一度だけ**返される（ラッチ動作）
- 呼び出し側（`rule_based_input.py`）で `_started_latch` を使って二重に保護
- 照明条件によってはRGB閾値の調整が必要

## 関連ファイル

- [rule_based_input.py](../Robot1/rule_based_input.py) - このモジュールを呼び出す
- [status_Robot.py](./status_Robot.md) - 状態定数の定義（現在は未活用）
