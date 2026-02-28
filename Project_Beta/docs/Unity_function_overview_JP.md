# Unity 機能概要 — Virtual Robot Race

このドキュメントは、Unityシミュレーター内部の処理フローと、Python側へ最終的に渡されるデータの概要を記述します。通信インターフェースの詳細は `Unity_Interface_Spec_JP.md` を参照してください。

---

## 1. Unityの役割

UnityはWebSocketサーバーとして動作し、以下の全てを管理します。

| 責務 | 内容 |
|------|------|
| 物理シミュレーション | ロボットの走行・旋回・衝突 |
| レース進行管理 | スタート判定・ラップカウント・終了条件 |
| バッテリーシミュレーション | 消費電力・衝突ペナルティの計算 |
| カメラ画像生成 | 車載カメラ映像のJPEGエンコードと送信 |
| データ記録 | Tick単位の時系列データ蓄積 |
| Python通信 | 制御コマンド受信・状態データ送信 |

---

## 2. 起動・接続シーケンス

```
Unity起動
  │
  ├─ GameManager.Start()
  │    ├─ TickScheduler生成 (50ms = 20fps)
  │    └─ PlayerCameraRGB を Tick に登録
  │
  ├─ WebSocketServer.Start()
  │    ├─ ポート12346でWebSocketサーバー開始 (/robot)
  │    └─ シーン内の全ロボット(R1〜R5)を自動検出・非表示化
  │
Python接続 ("connection" メッセージ受信)
  │    ├─ ロボットID・プレイヤー名・モード・raceFlag を設定
  │    ├─ active_robots リストを受信 → 参加ロボットのみ表示・有効化
  │    └─ 接続確認レスポンスを返信
  │
Python "ready" メッセージ受信 (全ロボット揃うまで待機)
  │
RaceManager: レーススタートシーケンス開始
  │    ├─ DataLogger を各ロボットに生成・Tickに登録
  │    └─ RaceStartLights でカウントダウン点灯
  │
"GO" 信号発火 → レース開始タイム確定
```

---

## 3. Tick駆動処理 (20fps / 50msごと)

`TickScheduler` が50msごとに `OnTick` イベントを発火し、以下が連動して動作します。

```
OnTick(tickIndex, utcMs)
  │
  ├─ PlayerCameraRGB.HandleTick()
  │    └─ RenderTextureからピクセル読み取り → JPEG変換 → WebSocketでバイナリ送信
  │
  └─ DataLogger.HandleTick()
       └─ 1行のデータを記録 (位置・姿勢・SOC・操舵値・衝突情報 等)
```

---

## 4. 主要コンポーネントと処理内容

### 4.1 WebSocketServer
Python からのメッセージを受信し、Unityの各コンポーネントに振り分けます。

**受信処理:**
- `"control"` メッセージ → `DriveAndSteerController.SetTorque()` / `ApplySteer()` を呼び出し
- `"connection"` メッセージ → ロボット登録、active_robots処理
- `"force_end"` メッセージ → レース強制終了

**送信処理:**
- カメラ画像 (バイナリ) → 各ロボットのPythonクライアントへ
- SOCデータ (JSON) → 定期送信
- レース終了時メタデータ (JSON) → 1回だけ送信

---

### 4.2 DriveAndSteerController
Pythonから受信した制御値を物理エンジン (WheelCollider) に適用します。

**入力:**
- `driveTorque` (-1.0〜+1.0) : 後輪の駆動トルク指令値

**内部処理:**
- 平滑化フィルター (`smoothing=0.2`) でコマンドをなめらかにする
- バッテリー残量ゼロ時はトルク強制ゼロ
- 後輪2つに `motorTorque` を適用 (最大120Nm)
- 前輪2つに `steerAngle` を適用 (最大±30度)

**DataLoggerへの出力:**
- `GetCurrentDriveTorque()` → 正規化済み値 (-1〜1)
- `GetCurrentSteerAngleRad()` → ラジアン値

---

### 4.3 BatteryManager
走行中の消費電力と衝突ペナルティをシミュレートします。

**消費モデル:**
- 毎フレーム: `totalTorque × deltaTime` を消費 (左右輪の絶対値合計)
- 衝突ペナルティ: `maxCapacity × fraction` を即時減算

**状態:**
- `soc` (0.0〜1.0) : 現在の充電率
- `IsDepleted()` : バッテリー切れフラグ → Unityが制御コマンドを無視する

---

### 4.4 RobotStatus
各ロボットのレース状態を管理します。

**追跡する状態:**
| 状態名 | 意味 |
|--------|------|
| `StartSequence` | カウントダウン中 |
| `Running` | 走行中 |
| `Lap1` / `Lap2` ... | ラップ通過後 |
| `Finish` | 規定周回完走 |
| `FalseStart` | フライング検出 → 失格 |
| `Fallen` | コース外落下 → 退場 |
| `BatteryDepleted` | バッテリー切れ → 障害物化 |
| `ForceEnd` | 強制終了 |

**フライング検出:**
- GO前に初期位置から0.05m以上移動した場合に自動検出

**落下検出:**
- Y座標が -0.1m 未満になった場合に検出

**衝突データの集計 (Beta 1.5):**
- `RecordCollisionForFrame()` で1フレーム内の衝突を蓄積
- `ConsumeCollisionData()` でDataLoggerが読み出し (読み取り後にリセット)

---

### 4.5 BodyCollisionHandler
ロボット本体の衝突を検知し、物理応答とバッテリーペナルティを適用します。

**衝突の種類と処理:**

| 衝突相手 | 速度応答 | ペナルティ計算 |
|----------|----------|----------------|
| 壁 | 衝突法線方向に速度反転 | `k × v² × 1.0`（自己責任100%） |
| 他ロボット | 反発方向に速度変更 | `k × |v_rel|² × R`（接近方向の責任比率） |

- クールダウン1秒：同じ衝突ペアは1秒以内に再計算しない
- ペナルティはBatteryManagerに即時反映される

---

### 4.6 GateTrigger
コース上のゲートを通過したときにラップカウントを更新します。

**ゲート構成:**
- Gate 0: スタートゲート（初回通過でレース計測開始）
- Gate 1, 2: フィニッシュゲート（Gate1 → Gate2 の順で通過 = 1周カウント）

逆走（Gate2 → Gate1）はラップ数を減算します。

---

### 4.7 PlayerCameraRGB
ロボット搭載カメラの映像をキャプチャしてPythonへ送信します。

**処理フロー (Tickごと):**
1. カメラのオフセット位置に追従移動
2. `RenderTexture` からピクセルデータを読み取り
3. JPEG形式にエンコード (224×224px, 品質85%)
4. WebSocketでバイナリメッセージとして該当ロボットのクライアントへ送信

送信は非同期 (`SendAsync`) で行われ、Python側の処理速度に影響されません。

---

### 4.8 DataLogger
Tickごとに1行のデータを内部リストに蓄積し、レース終了時にCSVとして出力します。

**1行に記録されるデータ:**

| フィールド | 内容 |
|-----------|------|
| `id` | Tickの連番インデックス |
| `session_time_ms` | セッション開始からの経過時間[ms] |
| `race_time_ms` | GOシグナルからの経過時間[ms] |
| `filename` | 対応する画像ファイル名 (`frame_XXXXXX.jpg`) |
| `soc` | バッテリー残量 (0.0〜1.0) |
| `drive_torque` | 駆動トルク (-1.0〜+1.0) |
| `steer_angle` | 操舵角 [rad] |
| `status` | ロボットの状態文字列 |
| `pos_z`, `pos_x`, `pos_y` | 3D座標 [m] (Z:前方, X:右, Y:上) |
| `yaw` | ヨー角 [度] (前進方向=0, 右=+) |
| `error_code` | エラーコード |
| `collision_type` | `"wall"` / `"robot"` / `"both"` / `""` |
| `collision_penalty` | 衝突ペナルティ率 (0.0〜) |

---

### 4.9 RaceManager
レース全体のライフサイクルを管理します。

**レース終了条件 (いずれか):**
1. 全ロボットが規定周回 (goalLap) を完走
2. 全ロボットが何らかの理由で「完了」状態（Finish/Fallen/FalseStart/BatteryDepleted）
3. タイムアウト (90秒)
4. `force_end` コマンド受信

**終了時処理:**
1. 制御コマンドの受付を停止
2. 各DataLoggerの最終行を `status="Finish"` に確定
3. CSVデータとUnityログを組み合わせてメタデータを生成
4. 各Pythonクライアントへ `type: "metadata"` を送信

---

## 5. Unity内部データの流れ（全体像）

```
Python
  │  "control" (driveTorque, steerAngle)
  ▼
WebSocketServer
  │  ApplyControl()
  ▼
DriveAndSteerController ←─────────────── BatteryManager
  │  SetTorque / ApplySteer              (IsDepleted → トルクゼロ)
  │  smoothing適用
  ▼
WheelCollider (Unityの物理エンジン)
  │  ロボット移動・旋回
  ▼
┌─ GateTrigger ────────────────→ RobotStatus (lapCount更新)
│
├─ BodyCollisionHandler ────────→ BatteryManager (penalty適用)
│                           └──→ RobotStatus (collisionData記録)
│
└─ RobotStatus (位置・状態監視)
     │  y<-0.1 → Fallen
     │  フライング検出 → FalseStart
     │  lapCount>=goalLap → Finish

[Tickごと (50ms)]
  ├─ PlayerCameraRGB → JPEG → WebSocket → Python (バイナリ)
  └─ DataLogger → 1行記録 (位置・SOC・操舵・衝突データ)

[レース終了時]
  RaceManager → DataLogger (CSV生成) → WebSocket → Python (metadata JSON)
```

---

## 6. Pythonへ最終的に送信されるデータ一覧

| タイミング | データ種別 | 形式 | 内容 |
|-----------|-----------|------|------|
| 接続直後 | 接続確認 | JSON | `type:"connection"`, status, message |
| Tickごと (50ms) | カメラ画像 | バイナリ | 224×224 JPEG (車載カメラ映像) |
| 定期送信 | バッテリー残量 | JSON | `type:"soc"`, soc (0.0〜1.0) |
| レース終了時 (1回) | レースメタデータ | JSON | `type:"metadata"`, csv_data, unity_log |

### メタデータCSVのカラム構成

```
id,session_time_ms,race_time_ms,filename,soc,drive_torque,steer_angle,status,pos_z,pos_x,yaw,pos_y,error_code,collision_type,collision_penalty
```

> **注意**: CSVのpos_z/pos_xの順はUnityの座標系（Z=前後方向、X=左右方向）に対応しています。

---

## 7. スクリプト一覧と役割サマリー

| スクリプト | 主な役割 |
|-----------|---------|
| `GameManager.cs` | システム全体の初期化・終了フロー |
| `WebSocketServer.cs` | WebSocketサーバー・メッセージルーティング |
| `RaceManager.cs` | レース進行・終了判定・メタデータ送信 |
| `TickScheduler.cs` | 50ms周期のタイマーイベント発火 |
| `DriveAndSteerController.cs` | 制御コマンドを物理エンジンに適用 |
| `BatteryManager.cs` | SOCの消費・ペナルティ計算 |
| `RobotStatus.cs` | ロボット状態(ラップ・転倒・フライング等)管理 |
| `BodyCollisionHandler.cs` | 衝突検知・物理応答・ペナルティ計算 |
| `GateTrigger.cs` | ゲート通過検知・ラップカウント更新 |
| `PlayerCameraRGB.cs` | カメラ画像キャプチャ・JPEG送信 |
| `DataLogger.cs` | Tick単位データ記録・CSV生成 |
| `TailLampController.cs` | テールランプ表示 (操舵→色相、スロットル→輝度) |
