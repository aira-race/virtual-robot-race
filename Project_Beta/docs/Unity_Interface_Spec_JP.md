# Unity インターフェース仕様書

このドキュメントは、Python制御スクリプトとUnityベースのVirtual Robot Raceシミュレーター間の通信インターフェースの概要を説明します。

## 1. 概要

このシステムは、主に2つのコンポーネントで構成されています。
- **Unityアプリケーション (サーバー)**: ロボットのシミュレーション、物理演算、環境のレンダリングを実行する、クローズドソースのWindows実行ファイルです。WebSocketサーバーとして機能します。
- **Pythonスクリプト (クライアント)**: ロボットの振る舞いを制御するオープンソースのPythonスクリプトです。手動制御、ルールベースのアルゴリズム、AIモデルなどが含まれます。PythonスクリプトはWebSocketクライアントとして機能します。

これら2つのコンポーネント間の通信は、WebSocket接続を介してリアルタイムで行われます。

## 2. 通信プロトコル

- **プロトコル**: WebSocket
- **URL**: `ws://<HOST>:<PORT>/robot`
- **デフォルト値** (`config.txt`より):
  - `HOST`: `localhost`
  - `PORT`: `12346`
- **デフォルトURL**: `ws://localhost:12346/robot`

接続はPythonクライアントからUnityサーバーに対して開始されます。

## 3. Python (クライアント) から Unity (サーバー) へのメッセージ

特に指定がない限り、すべてのメッセージはJSONオブジェクトです。各メッセージには `type` フィールドが含まれている必要があります。

### 3.1 ハンドシェイク (`type: "connection"`)
クライアントがサーバーに接続した直後に、ロボットを登録するために一度だけ送信されます。

**フィールド:**
- `type` (string): `"connection"`
- `robot_id` (string): ロボットの一意な識別子 (例: `"R1"`, `"R2"`)。
- `player_name` (string): 表示およびレース結果の投稿に使用されるプレイヤー名。
- `mode` (string): ロボットが実行されている制御モード (例: `"keyboard"`, `"ai"`)。
- `race_flag` (integer): ロボットがレースに参加する場合は `1`、観戦のみの場合は `0`。
- `active_robots` (list[int], optional): 現在のセッションでアクティブなすべてのロボット番号のリスト (例: `[1, 2]`)。通常、最初に接続したロボットのみが送信します。

**例:**
```json
{
  "type": "connection",
  "robot_id": "R1",
  "player_name": "Player0001",
  "mode": "ai",
  "race_flag": 1,
  "active_robots": [1, 2]
}
```

### 3.2 準備完了シグナル (`type: "ready"`)
クライアントが自身の初期化（例：AIモデルの読み込み）を完了した後に送信されます。Unityサーバーは、レースのカウントダウンを開始する前に、宣言されたすべての `active_robots` がこのシグナルを送信するのを待ちます。

**フィールド:**
- `type` (string): `"ready"`
- `robot_id` (string): 準備が完了したロボットのID。
- `message` (string): 説明的なメッセージ (例: `"AI model loaded and CUDA warmed up"`)。

**例:**
```json
{
  "type": "ready",
  "robot_id": "R1",
  "message": "AI model loaded and CUDA warmed up"
}
```

### 3.3 制御コマンド (`type: "control"`)
ロボットのモーターを制御するために、定期的（通常20Hz）に送信されます。

**フィールド:**
- `type` (string): `"control"`
- `robot_id` (string): 制御対象のロボットのID。
- `driveTorque` (float): 駆動輪に加えるトルクを-1.0から1.0の範囲で正規化した値。
- `steerAngle` (float): 前輪の操舵角をラジアン単位で指定した値。多くの実装では、約±30度に相当する-0.524から0.524の範囲に制限されます。

**例:**
```json
{
  "type": "control",
  "robot_id": "R1",
  "driveTorque": 0.5,
  "steerAngle": -0.262
}
```
> `-0.262 rad` は約 **-15度（左15度）** に相当します。負の値が左方向、正の値が右方向です。

### 3.4 強制終了 (`type: "force_end"`)
ユーザーが手動でPythonクライアントを停止したとき（例：「q」キーを押したとき）に送信されます。これはサーバーにレースを正常に終了させ、最終的なメタデータを送り返すよう指示します。

**フィールド:**
- `type` (string): `"force_end"`
- `robot_id` (string): 停止を開始したロボットのID。
- `message` (string): セッションが終了する理由についての説明的なメッセージ。

**例:**
```json
{
  "type": "force_end",
  "robot_id": "R1",
  "message": "Python client force-ended with 'q' key"
}
```

## 4. Unity (サーバー) から Python (クライアント) へのメッセージ

### 4.1 接続確認 (`type: "connection"`)
クライアントのハンドシェイクメッセージに対するサーバーの応答。

**フィールド:**
- `type` (string): `"connection"`
- `status` (string): 接続試行の結果 (例: `"success"`)。
- `message` (string): サーバーからの説明的なメッセージ。

**例:**
```json
{
  "type": "connection",
  "status": "success",
  "message": "Robot R1 connected successfully"
}
```

### 4.2 バッテリー残量 (`type: "soc"`)
サーバーから定期的に送信され、ロボットのバッテリーレベルを提供します。

**フィールド:**
- `type` (string): `"soc"`
- `soc` (float): バッテリーの現在の充電状態。通常は0.0から1.0の範囲。

**例:**
```json
{
  "type": "soc",
  "soc": 0.88
}
```

### 4.3 レース終了時のメタデータ (`type: "metadata"`)
レース終了時（または `force_end` リクエスト後）に一度だけ送信されます。これには、実行中にUnityによってログに記録されたすべてのデータが含まれています。

**フィールド:**
- `type` (string): `"metadata"`
- `csv_data` (string): CSV形式のレース全体のティックごとのデータを含む単一の文字列。文字列内の改行や引用符はエスケープされます (`
`, `"`)。
- `unity_log` (string): セッション中にUnityによって生成されたログを含む単一の文字列。改行はエスケープされます。

### 4.4 画像データ (バイナリメッセージ)
JSONメッセージに加えて、サーバーはカメラ画像を生のバイナリWebSocketメッセージとしてクライアントにストリーミングします。
- **フォーマット**: 各メッセージは、単一のJPEGエンコード画像を表すバイト配列です。
- **頻度**: 画像ストリームの頻度はUnityシミュレーションで設定されます。
- **処理**: Pythonクライアントはこれらを `bytes` として受信し、JSONテキストメッセージとは別に処理する必要があります。
