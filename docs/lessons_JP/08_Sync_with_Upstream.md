# 8. Upstreamとの同期

## はじめに

aira公式リポジトリは、新機能の追加やバグ修正のために定期的に更新されます。
あなたが [レッスン00](00_Preparation.md) でフォークしたリポジトリは、フォーク時点のスナップショットです。そのままでは公式の更新は自動的に反映されません。

このレッスンでは、**自分のアルゴリズムを守りながら、公式の最新版を取り込む方法**を学びます。

---

## Upstreamとは？

Gitでは、リモートリポジトリに名前をつけて管理します。

| 名前 | 指す場所 | 役割 |
|------|---------|------|
| `origin` | あなたのフォーク（GitHub上） | 自分の作業を保存・共有する場所 |
| `upstream` | aira公式リポジトリ | 最新のシミュレーターを取得する場所 |

フォーク直後は `origin` しか存在しません。`upstream` を手動で追加することで、公式の更新を取り込めるようになります。

---

## 手順

### Step 1: upstreamを追加する（初回のみ）

```bash
git remote add upstream https://github.com/aira-race/virtual-robot-race.git
```

追加できたか確認します。

```bash
git remote -v
```

以下のように表示されれば成功です。

```
origin    https://github.com/あなたのユーザー名/virtual-robot-race.git (fetch)
origin    https://github.com/あなたのユーザー名/virtual-robot-race.git (push)
upstream  https://github.com/aira-race/virtual-robot-race.git (fetch)
upstream  https://github.com/aira-race/virtual-robot-race.git (push)
```

---

### Step 2: ローカルの変更を退避する

`config.txt` など、自分が編集中のファイルがある場合、そのままでは merge がブロックされます。

```
error: Your local changes to the following files would be overwritten by merge:
        config.txt
```

このエラーが出たら、まず変更を一時退避します。

```bash
git stash
```

> **💡 `git stash` とは**: 作業中の変更を一時的に棚上げするコマンドです。merge 後に `git stash pop` で元に戻せます。

---

### Step 3: 公式の最新版を取得・マージする

aira公式リポジトリの更新を取り込みます。

```bash
git fetch upstream
git merge upstream/main
```

- `git fetch upstream` — 公式の変更をローカルに取得します（まだ自分のコードには反映されません）
- `git merge upstream/main` — 取得した変更を自分のブランチに統合します

> **💡 自分のコードは消えません**: `merge` は公式の変更と自分の変更を**統合**します。同じファイルの同じ行を両方が編集していた場合のみ「コンフリクト（競合）」が発生します（後述）。

merge が完了したら、退避した変更を戻します。

```bash
git stash pop
```

---

### Step 4: 自分のoriginに反映する

マージが完了したら、自分のGitHub上のフォークにも反映します。

```bash
git push origin main
```

---

## コンフリクト（競合）が発生した場合

公式の更新が、あなたが編集したファイルの同じ箇所に変更を加えていた場合、コンフリクトが発生します。

コンフリクトが起きたファイルはこのような表示になります。

```
<<<<<<< HEAD
# あなたの変更
=======
# 公式の変更
>>>>>>> upstream/main
```

**対処の流れ：**

1. VSCodeでコンフリクトしているファイルを開く
2. 残したい内容を選ぶ（両方残すことも可能）
3. `<<<<<<`, `=======`, `>>>>>>>` の行を削除して保存
4. `git add` → `git commit` で完了

> **💡 Gemini Code Assist に相談する**: コンフリクトの内容をそのまま貼り付けて「どちらを残すべきか」を聞くと、的確なアドバイスをもらえます。

---

## まとめ

| やること | コマンド | タイミング |
|---------|---------|-----------|
| upstreamを登録 | `git remote add upstream <URL>` | 初回のみ |
| ローカル変更を退避 | `git stash` | merge前（変更がある場合） |
| 公式の更新を取得 | `git fetch upstream` | 更新があるとき |
| 自分のブランチに統合 | `git merge upstream/main` | 更新があるとき |
| 退避した変更を戻す | `git stash pop` | merge完了後 |
| 自分のフォークに反映 | `git push origin main` | merge完了後 |

aira のバージョンアップ情報は [GitHub Releases](https://github.com/aira-race/virtual-robot-race/releases) や [X (@RaceYourAlgo)](https://x.com/RaceYourAlgo) でお知らせします。

---

⬅️ [前のレッスン: 07_How_to_Join_Race.md（レースに参加する）](07_How_to_Join_Race.md) ｜ [用語集](99_Glossary.md)
