# aira 研修 前提条件

**対象**: aira Beta 1.6 を使用した大学研修
**最終更新**: 2026-02-15

---

## 1. ハードウェア要件

| 項目 | 必須 | 推奨 | 備考 |
|------|------|------|------|
| **OS** | Windows 10 以上 | Windows 11 | Mac/Linux は未対応 |
| **RAM** | 8 GB | 16 GB | torch + Unity 同時起動のため |
| **ディスク空き** | 5 GB | 10 GB | .venv 約2.5GB + Unity 約1GB + 走行データ |
| **ストレージ** | HDD 可 | SSD | 画像保存時の I/O 性能に影響 |
| **GPU** | 不要 | NVIDIA GeForce (CUDA対応) | ルールベース/キーボードなら CPU のみで OK。AI 訓練時は GPU 推奨 |
| **ネットワーク** | **必須** | 有線 LAN | pip install (約2.5GB DL)、GAS POST に必要 |
| **画面解像度** | 1366x768 | 1920x1080 | Unity 画面 + VSCode 同時表示 |

---

## 2. ソフトウェア要件（事前インストール）

| ソフトウェア | バージョン | 入手先 | インストール時の注意 |
|------------|----------|-------|-------------------|
| **Python** | 3.12 以上 (64bit) | https://www.python.org/downloads/ | **「Add Python to PATH」に必ずチェック** |
| **VSCode** | 最新版 | https://code.visualstudio.com/ | 日本語パック推奨 |
| **Git** | 最新版 | https://git-scm.com/ | デフォルト設定で OK |
| **Web ブラウザ** | Chrome / Edge | - | リーダーボード確認用 |

### インストール確認コマンド

```bash
python --version    # Python 3.12.x と表示されれば OK
git --version       # git version 2.x.x と表示されれば OK
code --version      # VSCode バージョンが表示されれば OK
```

> **最大のつまずきポイント**: Python インストール時に「Add Python to PATH」にチェックを入れ忘れると、`python` コマンドが認識されず全ての手順が失敗します。必ず確認してください。

---

## 3. 前提スキル

### 必須スキル（これがないと研修が進まない）

| スキル | 具体的にできること | 確認方法 |
|--------|-----------------|---------|
| **PC 基本操作** | フォルダ作成、ファイルコピー、エクスプローラー操作 | - |
| **テキスト編集** | 設定ファイル (.txt) を開いて値を変更して保存 | メモ帳で編集できるか |
| **ターミナル操作** | コマンドを見てコピー＆ペーストして実行できる | `python --version` を実行できるか |

### 研修中に習得するスキル（事前知識不要）

| スキル | 研修のどこで学ぶか |
|--------|---------------|
| Git clone | Step 1: リポジトリ取得 |
| VSCode でフォルダを開く | Step 1: プロジェクト開始 |
| VSCode ターミナル操作 | Step 1: setup_env.bat 実行 |
| 設定ファイルの読み書き | Step 2: robot_config.txt 編集 |
| Python 仮想環境 (.venv) | Step 1: 自動構築される |
| CSV データの構造理解 | Step 4: metadata.csv 確認 |
| AI Coding Extension | Step 6: アクティベーション |

---

## 4. 検証済み環境

| # | OS | CPU | GPU | RAM | 結果 |
|---|-----|-----|-----|-----|------|
| 1 | Windows 11 | Core i5-12450H | RTX 3060 Laptop | 16 GB | 快適 |
| 2 | Windows 11 | Core i5 (8th Gen) | Intel UHD 620 (内蔵) | 8 GB | 動作 OK（AI 推論も可） |
| 3 | Windows 11 Home | Ryzen 7 5800X | RTX 3080 Ti 12GB | 32 GB | 動作 OK |
| 4 | Windows 11 Home | Core i7-1260P (12th Gen) | Intel Iris Xe (内蔵) | 16 GB | 動作 OK |
| 5 | Windows 11 Pro | Core i9-11900KF | RTX 3070 | 32 GB | 動作 OK |

> **ポイント**: #2, #4 のように **GPU なし（内蔵グラフィックのみ）でも動作確認済み**。ルールベース・キーボード操作であれば専用 GPU は不要です。

---

## 5. 研修当日の動作確認フロー

### Step 1: Clone & 環境構築（合否判定）

```bash
git clone https://github.com/AAgrandprix/virtual-robot-race.git
cd virtual-robot-race/Project_Beta
setup_env.bat
```

**合否判定基準:**
- `.venv` フォルダが生成されている
- ターミナルに `(.venv)` が表示される

### Step 2: NAME 設定

`Robot1/robot_config.txt` を VSCode で開き、`NAME=Player0000` を自分の名前に変更。

### Step 3: main.py 実行

```bash
python main.py
```

**確認項目:**
- Unity が自動起動する
- 2台のルールベース AI ロボットが走り出す
- レース終了後、エクスプローラーが開く

### Step 4: 出力データ確認

- `Robot1/training_data/run_YYYYMMDD_HHMMSS/metadata.csv` が存在する
- `Robot1/training_data/run_YYYYMMDD_HHMMSS/output_video.mp4` が存在する

### Step 5: AI Extension アクティベーション

- Gemini Code Assist または Claude Code の導入
- カレントディレクトリが `Project_Beta` であることを確認
