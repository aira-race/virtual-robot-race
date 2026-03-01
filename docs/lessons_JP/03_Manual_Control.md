# 3. マニュアル操作

ここでは、`main.py`を起動して、キーボード操作でロボットを動かすレッスンをします。

## 1. 事前準備

レッスンを始める前に、2つの設定ファイルを確認・変更します。`README.md`の書式を参考に、コードブロック形式で説明します。

### 1. 走行するロボットの選択 (`config.txt`)
**ルートフォルダ**（クローン時に作成された `virtual-robot-race` フォルダ）にある `config.txt` を編集します。
今回はロボット1台で練習するため、以下のように設定してください。

```ini
# config.txt
ACTIVE_ROBOTS=1
```

> **⚠️ 保存を忘れずに！** 編集後は必ずファイルを保存（`Ctrl+S`）してください。保存しないと変更が反映されません。

### 2. ロボットの個別設定 (`Robot1/robot_config.txt`)
`Robot1` フォルダにある `robot_config.txt` を編集します。
キーボードで操作し、ログを保存する設定は以下の通りです。

```ini

# Player name (up to 10 alphanumeric characters, used for leaderboard)
NAME=YourName　　# 自分の名前に変更してください

# Robot1/robot_config.txt
# Control mode:
# 1 = keyboard
# 2 = table (CSV playback)
# 3 = rule_based (autonomous lane following)
# 4 = ai (neural network inference)
# 5 = smartphone (smartphone controller via QR code)
MODE_NUM=1

# Data saving:
# 1 = Save CSV and JPEG images during run (also auto-creates MP4 video)
# 0 = Do not save data (faster, less disk usage, no video)
# Note: Video settings (FPS, etc.) are fixed in Python code for advanced users
DATA_SAVE=1

# Race participation flag:
# 1 = Participate in race (results will be posted)
# 0 = Test Run only (no results posted)
RACE_FLAG=0


```
> `YourName`の部分は、必ずご自身の名前に変更してください。

> 設定方法が不明な場合は、READMEを参照するか、[NotebookLM QAシステム](https://notebooklm.google.com/notebook/1a8a70f1-d30e-4bad-bd01-67b3219cfafa)で質問してください。

## 2. 基本ルール

レースの基本的なルールをおさらいしましょう。

- **スタート:** 赤いシグナルが3つ点灯し、その後すべて消灯します。消灯がスタートの合図です。
- **フライング:** スタート合図の前に動くとフライングとなり、失格になります。
- **周回:** コースを2周し、その合計タイムを競います。
- **逆走:** コースを逆走すると、周回数がマイナス1されてしまいます。
- **バッテリー (SOC):** 走行するとバッテリーを消費します。SOC（State of Charge）が0%になると走行不能になります。
- **衝突:** 壁や他のロボットに衝突すると、ペナルティとしてSOCが減少します。
- **コースアウト:** コースから落下すると失格です。
- **タイムアップ:** 90秒以内に2周を完了できない場合も、タイムアップで失格となります。

## 3. キーボード操作

- **前進／後退:** `W` / `Z`
- **操舵（左右）:** `J` / `L`
- **ステアリング中央:** `I`, `M`
    - *注: `J`キー、`L`キーを離すとステアリングは自動で中央に戻りますが、`I`キーや`M`キーで即座に中央に戻すこともできます。*

## 4. 画面の見方

### カメラ情報
画面分割されている場合、左側がRobot1、右側がRobot2のカメラ映像です。

### ターゲット表示
画面上にある丸い円は「ターゲット」です。これはキーボード入力（`W, Z, J, L`）をXY座標で可視化したものです。
例えば、前進トルク1、ステアリング中央の場合、ターゲットは座標 (0, 1) に移動します。

### ロボット背面のランプ
後続のロボットに対して、自分の操作（アクセル、ステアリング、後退）を伝えるための重要なインターフェースです。これは単なる飾りではなく、レース戦略に関わる「視覚的なログ」としての役割を持ちます。

- **色（Hue）:** ステアリングの方向を示します。
    - **左:** 赤（Red）
    - **直進:** 緑（Green）
    - **右:** 青（Blue）
    - 左右それぞれ、曲がる量に応じて緑からの色変化が大きくなります。

- **光の高さ（ゲージ）:** 前進アクセルの強さ（トルク）を示します。
    - **アクセルOFF:** 光は消えます。
    - **アクセルON:** 踏み込み量に応じて、ゲージが下から上へ伸びます。

- **点滅:** バック（後退）していることを示す、最も重要な警告です。
    - バック中は、光の高さは**常に最大**となり、**周期的に点滅**します。
    - 注意点として、バック中もステアリング方向に応じて**色は変化し続けます**。

## 5. レッスン課題

以下のステップでマニュアル操作に慣れていきましょう。
毎回、**① config設定 → ② robot_config設定 → ③ 保存 → ④ `python main.py` 実行** の流れで進めます。

1.  **Robot1で2周完走を目指す**
    - `config.txt`: `ACTIVE_ROBOTS=1`
    - `Robot1/robot_config.txt`: `MODE_NUM=1`
    - 保存して `python main.py` を実行し、2周完走を目指しましょう。

2.  **Robot2で2周完走を目指す**
    - `config.txt`: `ACTIVE_ROBOTS=1`（1台のまま）
    - `Robot2/robot_config.txt`: `MODE_NUM=1`
    - Robot2のキーボード操作で2周を目指しましょう。

3.  **失敗を体験する**
    - フライング、コースアウト、衝突によるバッテリー切れなど、様々な失格パターンを意図的に試してみましょう。ペナルティの仕組みを体で覚えます。

4.  **AIと併走する**
    - `config.txt`: `ACTIVE_ROBOTS=2`
    - `Robot1/robot_config.txt`: `MODE_NUM=1`（自分がキーボード操作）
    - `Robot2/robot_config.txt`: `MODE_NUM=4`（AIが自動走行）
    - AIの走りを観察しながら、後ろから追走してみましょう。

5.  **タイムアタック**
    - `config.txt`: `ACTIVE_ROBOTS=1`
    - `Robot1/robot_config.txt`: `MODE_NUM=1`
    - 2周の合計タイムを競いましょう。誰が一番速いか挑戦！

