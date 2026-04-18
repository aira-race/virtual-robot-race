# 8. Syncing with Upstream

## Introduction

The official aira repository is updated regularly with new features and bug fixes.
The repository you forked in [Lesson 00](00_Preparation.md) is a snapshot from the time of forking — it does not automatically receive updates from the official repo.

In this lesson, you will learn how to **pull in the latest official changes while keeping your own algorithm safe**.

---

## What is Upstream?

In Git, remote repositories are managed by name.

| Name | Points to | Purpose |
|------|-----------|---------|
| `origin` | Your fork (on GitHub) | Where you save and share your work |
| `upstream` | The official aira repository | Where you fetch the latest simulator updates |

Right after forking, only `origin` exists. By manually adding `upstream`, you can pull in updates from the official repository.

---

## Steps

### Step 1: Add upstream (first time only)

```bash
git remote add upstream https://github.com/aira-race/virtual-robot-race.git
```

Verify it was added:

```bash
git remote -v
```

You should see something like:

```
origin    https://github.com/YOUR_USERNAME/virtual-robot-race.git (fetch)
origin    https://github.com/YOUR_USERNAME/virtual-robot-race.git (push)
upstream  https://github.com/aira-race/virtual-robot-race.git (fetch)
upstream  https://github.com/aira-race/virtual-robot-race.git (push)
```

---

### Step 2: Stash your local changes

If you have uncommitted changes (e.g., in `config.txt`), the merge will be blocked:

```
error: Your local changes to the following files would be overwritten by merge:
        config.txt
```

If you see this error, stash your changes first:

```bash
git stash
```

> **💡 What is `git stash`?** It temporarily shelves your uncommitted changes. After the merge, run `git stash pop` to restore them.

---

### Step 3: Fetch and merge the latest official changes

```bash
git fetch upstream
git merge upstream/main
```

- `git fetch upstream` — Downloads the official changes locally (nothing in your code changes yet)
- `git merge upstream/main` — Integrates those changes into your branch

> **💡 Your code is safe**: `merge` combines the official changes with yours. A conflict only occurs if both you and the official repo edited the same line of the same file (see below).

Once the merge is complete, restore your stashed changes:

```bash
git stash pop
```

---

### Step 4: Push to your origin

Push the merged result to your fork on GitHub:

```bash
git push origin main
```

---

## Resolving Conflicts

If the official update changed the same part of a file you also edited, a conflict will occur.

A conflicted file looks like this:

```
<<<<<<< HEAD
# Your change
=======
# Official change
>>>>>>> upstream/main
```

**How to resolve:**

1. Open the conflicting file in VSCode
2. Choose which version to keep (or combine both)
3. Delete the `<<<<<<`, `=======`, and `>>>>>>>` marker lines and save
4. Run `git add` → `git commit` to finalize

> **💡 Ask Gemini Code Assist**: Paste the conflict directly and ask "which version should I keep?" — it will give you a clear recommendation.

---

## Summary

| Action | Command | When |
|--------|---------|------|
| Register upstream | `git remote add upstream <URL>` | First time only |
| Stash local changes | `git stash` | Before merge (if you have local edits) |
| Fetch official updates | `git fetch upstream` | When updates are available |
| Merge into your branch | `git merge upstream/main` | When updates are available |
| Restore stashed changes | `git stash pop` | After merge |
| Push to your fork | `git push origin main` | After merge |

aira version updates are announced on [GitHub Releases](https://github.com/aira-race/virtual-robot-race/releases) and [X (@RaceYourAlgo)](https://x.com/RaceYourAlgo).

---

⬅️ [Previous lesson: 07_How_to_Join_Race.md (How to Join the Race)](07_How_to_Join_Race.md) ｜ [Glossary](99_Glossary.md)
