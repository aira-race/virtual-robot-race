# 0. 事前準備

## はじめに
こんにちは！このレッスンでは、仮想ロボットレースプラットフォーム「aira」で、AIやルールベースの制御プログラムを開発する方法を学びます。
この最初のセッションでは、開発に必要な環境をあなたのPCに構築します。

**作業時間の目安**: 約10分（※Pythonライブラリ等のダウンロード時間を除く）

スムーズなレッスン開始のため、一つずつ確認しながら進めましょう。

*   **そもそも「aira」とは？** -> [コンセプト紹介](https://www.youtube.com/watch?v=wAaaAODsfrE&t=26s)
*   **動画で見る環境構築ガイド** -> [aira-race.com/getting-started](https://aira-race.com/getting-started)

aira:autonomous intelligence racing arena

---

## 対象となる方

本レッスンは、以下のような方を対象としています。

*   AI、自動運転、ロボット制御といった分野に興味があり、実際に手を動かして学んでみたい、大学3年生以上の方、および社会人の方。
*   Pythonのプログラミング経験は問いません。ただし、基本的なPC操作（タイピング、ファイルのコピー＆ペースト、ターミナルでのコマンド実行など）はスムーズに行えることを前提とします。
*   レッスンで使用するGoogle社のAIサービス（Gemini Code Assist等）の利用規約に同意し、ご自身のアカウントで利用可能な方（18歳以上であることが推奨されます）。

---

## 1. 開発環境の要件　
まず、レッスンに必要なハードウェアとソフトウェアの要件を確認します。

### ハードウェア要件

| 項目 | 必須 | 推奨 | 備考 |
|------|------|------|------|
| **OS** | Windows 11 | - | Mac/Linux は未対応 |
| **RAM** | 8 GB | 16 GB | AI(torch) + Unity 同時起動のため |
| **ディスク空き** | 5 GB | 10 GB | .venv 約2.5GB + Unity 約1GB + 走行データ |
| **GPU** | 不要 | NVIDIA GeForce (CUDA対応) | AI訓練時にGPU推奨 |
| **ネットワーク** | **必須** | - | ライブラリインストール(約2.5GB)に必要 |

### ソフトウェア要件

| ソフトウェア | バージョン | 入手先 | インストール時の注意 |
|:---|:---|:---|:---|
| **Python** | 3.12 以上 (64bit) | [公式サイト](https://www.python.org/downloads/) | **「Add Python to PATH」に必ずチェック** |
| **VSCode** | 最新版 | [公式サイト](https://code.visualstudio.com/) | 日本語化パック推奨 |
| **Git** | 最新版 | [公式サイト](https://git-scm.com/) | デフォルト設定でOK |
| **Googleアカウント** | - | [作成ページ](https://accounts.google.com/signup) | NotebookLM, Gemini Code Assistで利用 |
| **GitHubアカウント**| - | [作成ページ](https://github.com/signup) | 開発環境のフォーク(Fork)で必須 |
| **PayPalアカウント** | - (オプション) | [作成ページ](https://www.paypal.com/signup) | 賞金のある大会に参加する場合に必要 |

> **⚠️ 最重要ポイント**
> Pythonインストール時に「**Add Python to PATH**」にチェックを入れ忘れると、`python` コマンドが認識されず、この後の手順がすべて失敗します。もし忘れてしまった場合は、一度アンインストールして再インストールしてください。

---

## 2. セットアップ手順
ここからが実際の手順です。自分のPC上に、自分専用の開発環境を構築していきます。

### Step 1: 自分用のリポジトリを準備 (Fork & Clone)

「Fork（フォーク）」とは、公式リポジトリの自分専用のコピーをGitHub上に作ることです。
「Clone（クローン）」とは、そのコピーを自分のPCにダウンロードすることです。

この2つの作業を、**GitHub Desktop**（無料アプリ）を使って行います。ターミナルのコマンドを入力する必要はありません。

1. **GitHub Desktop をインストールする**
    - まだインストールしていない場合は、先にインストールしてください。
    - → [GitHub Desktop をダウンロード](https://desktop.github.com/)
    - インストール後、GitHub アカウントでサインインします。

2. **公式リポジトリをフォークする**
    - ブラウザで [公式リポジトリ](https://github.com/aira-race/virtual-robot-race) を開きます。
    - 画面右上の **Fork** ボタンをクリックします。
    - 「Create fork」ボタンを押せば完了です。
    - これで `https://github.com/あなたのユーザー名/virtual-robot-race` という、あなた専用のリポジトリができました。

3. **GitHub Desktop でクローンする**
    - フォーク完了後、緑色の **Code** ボタンをクリックします。
    - **「Open with GitHub Desktop」** を選択します。
    - GitHub Desktop が開いたら、保存場所を確認して **Clone** ボタンを押します。
    - PC上に `virtual-robot-race` フォルダが作成されれば完了です。

> **💡 ターミナルでやりたい場合**: 以下のコマンドでも同じことができます。
> ```bash
> git clone https://github.com/あなたのユーザー名/virtual-robot-race.git
> ```

### Step 3: Python環境の構築
次に、ロボットを制御するPythonプログラムの開発環境を構築します。

1.  環境構築スクリプト `setup_env.bat` を実行します。
    ```bash
    .\setup_env.bat
    ```
    > **💡 `.\` の意味**: PowerShellでは、`setup_env.bat` とだけ入力しても「コマンド」として認識されません。`.\` は「**現在のフォルダにあるファイル**」を指定する記法で、「このフォルダの `setup_env.bat` を実行する」という意味になります。

    このスクリプトは、仮想環境の作成と、必要なPythonライブラリのインストールを自動で行います。スクリプトが正常に完了すると、仮想環境が有効化された**新しいコマンドプロンプト（黒いウィンドウ）が自動的に開きます**。プロンプトの行頭に `(.venv)` と表示されていれば成功です。

    > **💡 VS Code のターミナルで作業したい場合**: 自動で開く黒いウィンドウではなく、VS Code 内のターミナルで作業したい場合は、VS Code のターミナル（`Ctrl + Shift + @`）で以下のコマンドを実行してください。
    > ```bash
    > .venv\Scripts\activate
    > ```
    > プロンプトに `(.venv)` が表示されれば有効化完了です。以降の作業はこのターミナルで行います。

### Step 4: VS Code の設定
最後に、`Visual Studio Code` の設定を行います。

1.  **プロジェクトフォルダを開く**
    - VS Codeを起動し、「ファイル」>「フォルダーを開く」から、`virtual-robot-race` フォルダを選択します。

2.  **推奨拡張機能のインストール**
    - VS Codeの拡張機能マーケットプレイスで、以下の拡張機能を検索してインストールします。
      - **Python** (Microsoft提供): Python開発の必須ツールです。
      - **Gemini Code Assist** (Google Cloud提供): AIによるコーディング支援です。レッスンの後半で活用します。（※ログインにはGoogleアカウントを使用します）
      - **Markdown Preview Enhanced** (shd101wyy提供): このレッスンドキュメントを快適に読むための拡張機能です。`.md` ファイルを開いた状態で `Ctrl + Shift + V` を押すとプレビューが開き、**コードブロックの右上にコピーボタンが表示されます。**

    > **💡 ターミナルへの貼り付け**: VS Codeのターミナル上で **右クリック** するだけで貼り付けできます（`Ctrl+V` は不要です）。

3.  **Pythonインタープリターの選択**
    - `Ctrl + Shift + P` でコマンドパレットを開き、`Python: Select Interpreter` と入力します。
    - プロジェクトの仮想環境である `./.venv/Scripts/python.exe` を選択します。
    
    これで、VS Codeがプロジェクト用のPython環境を正しく認識するようになります。

---

## 3. GPU高速化 (オプション)
NVIDIA製のGPUを搭載したPCをお使いの場合、AIの学習や推論を高速化できます。

1.  `setup_env.bat`などで作成済みの仮想環境ターミナル（行頭に `(.venv)` が表示されているもの）を開きます。
2.  以下の**2つのコマンドを順番に**実行します。1行目でCPU版を削除し、2行目でGPU版をインストールします。
    ```bash
    pip uninstall torch torchvision -y
    ```
    ```bash
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
    ```
3.  以下のコマンドでGPUが認識されているか確認します。
    ```bash
    python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
    ```
    `CUDA available: True` と表示されれば成功です。

---

## 4. 動作確認

セットアップが正しく完了したか、実際に起動して確認しましょう。

1.  VS Codeで新しいターミナルを開きます（`Ctrl + Shift + @`）。プロンプトに `(.venv)` が表示されていることを確認してください。
2.  `start.bat` を実行します。
    ```bash
    .\start.bat
    ```
    > **💡 `python main.py` でも同じです。** `start.bat` は `.venv` を有効化してから `python main.py` を実行するショートカットです。すでに `(.venv)` が有効な場合はどちらでも構いません。
3.  以下の現象が起きることを確認してください。
    > **💡 初回起動時**: Windowsのセキュリティ（ファイアウォール）の許可ダイアログが表示される場合があります。**「アクセスを許可する」をクリック**して続行してください。UnityとPython間の通信に必要な設定です。

    - [ ] ランチャーウィンドウが開く。名前を**記入して** **START** をクリックする。
    - [ ] Unityのシミュレーター画面が**自動で起動**する。
    - [ ] 2台のロボットがコースを自動で走り始める（デフォルト: R1=ルールベース、R2=AI）。
    - [ ] レースが終了すると、Unity画面が自動で閉じる。

    > **💡 データ保存について**: デフォルトでは `DATA_SAVE=0`（保存なし）になっています。走行データを保存したい場合は `config.txt` の `DATA_SAVE=1` に変更してください（詳細はレッスン4で学びます）。

以上で開発環境の準備は完了です！お疲れ様でした。

> **❓ うまくいかない場合は？**
> [レッスン02：ライブQ&A（NotebookLM）](02_Live_QA_NotebookLM.md) でAIに質問できます。エラーメッセージをそのまま貼り付けると、原因と対処法を教えてくれます。

---

➡️ [次のレッスンへ: 01_Foundation.md（基礎概念）](01_Foundation.md)
