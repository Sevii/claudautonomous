---
name: repo-review
description: Diagnose an unfamiliar Git repository before reading code by running five git commands that reveal churn hotspots, ownership concentration, bug clustering, project momentum, and crisis patterns. Use when first dropped into a codebase, when reviewing or auditing a project for risk, or when deciding which files deserve attention first. Based on https://piechowski.io/post/git-commands-before-reading-code/.
---

# Repo Review — Git-First Codebase Diagnosis

Before opening a single source file, run five git commands to learn what the repository's *history* says about the *code*. The output points you at the highest-risk, highest-leverage files and surfaces team-level smells (bus factor, deployment anxiety, momentum loss) that no static read of the code will reveal.

Use this skill when:

- You are dropped into an unfamiliar repo and need to prioritize what to read.
- You are auditing or reviewing a project and want signals beyond the code itself.
- A maintainer asks "where is the risk?" and you need an evidence-based answer.

Reference: <https://piechowski.io/post/git-commands-before-reading-code/>

---

## Workflow

Run the five commands in order. Each takes seconds. Capture the output, then **cross-reference** — the real insight comes from files (or patterns) that show up on more than one list.

Run from the repo root unless noted. For command 1, `cd` into the primary source directory (`src/`, `app/`, `lib/`) first so lockfiles and generated assets don't dominate.

---

## 1. Code churn hotspots — *what gets touched the most?*

```bash
git log --format=format: --name-only --since="1 year ago" \
  | sort | uniq -c | sort -nr | head -20
```

Lists the 20 most-modified files over the past year.

**Read it like this:**

- A file at the top of this list with **no clear owner** is codebase drag — "every change is a patch on a patch."
- Configuration files, schema files, and top-level routers naturally churn; that's fine.
- A single business-logic file dominating the list is a refactor candidate or a god-object.

**Tip:** Run from `src/` or `app/` to exclude `package-lock.json`, `yarn.lock`, `Cargo.lock`, generated migrations, etc. If you want the whole repo but cleaner output, pipe through `grep -vE '(lock\.json|\.lock|dist/|build/)'`.

---

## 2. Bus factor & team ownership — *who actually writes this code?*

```bash
git shortlog -sn --no-merges
```

Ranks contributors by commit count across all history.

```bash
git shortlog -sn --no-merges --since="6 months ago"
```

Same ranking, but restricted to recent activity.

**Read it like this:**

- A single developer with **>60% of commits** is concentration risk — if they leave, institutional knowledge leaves with them.
- Compare the all-time list to the 6-month list. If the original architects are missing from the recent list, the people maintaining the code today probably did **not** design it.
- A long tail of one-commit contributors with no core team is also a smell — drive-by changes with nobody steering.

---

## 3. Bug clustering — *which files keep breaking?*

```bash
git log -i -E --grep="fix|bug|broken" --name-only --format='' \
  | sort | uniq -c | sort -nr | head -20
```

Lists the 20 files most often touched by commits whose message mentions a fix, bug, or breakage.

**Read it like this:**

- Files appearing on **both this list and the churn list (command 1)** are the highest-risk code in the repo — perpetually breaking and perpetually patched, but never properly resolved.
- This depends on commit-message discipline. If the team squashes everything as "update" or uses ticket IDs only (e.g. `JIRA-1234`), broaden the regex: `--grep="fix|bug|broken|hotfix|patch|issue"` or grep on PR titles instead.

---

## 4. Project momentum — *is this project alive?*

```bash
git log --format='%ad' --date=format:'%Y-%m' | sort | uniq -c
```

Prints monthly commit counts across the full history.

**Read it like this:**

- A **steady rhythm** — even a low one — is healthy. Cadence matters more than peak volume.
- A **declining trend** over the last 6–12 months signals momentum loss.
- **Sharp drops** often correlate with a key person leaving. Cross-reference with command 2's 6-month view.
- **Long gaps punctuated by spikes** suggest batched releases rather than continuous shipping — slower feedback loop, larger blast radius per change.

For a quick visual, pipe the output through `awk '{printf "%s %s\n", $2, $1}'` and eyeball the right column.

---

## 5. Crisis patterns — *how often does the team firefight?*

```bash
git log --oneline --since="1 year ago" \
  | grep -iE 'revert|hotfix|emergency|rollback'
```

Counts reverts, hotfixes, emergency commits, and rollbacks over the past year.

**Read it like this:**

- A handful per year is normal.
- **Several per month**, or clusters within days of each other, indicate systemic problems: unreliable tests, slow CI, difficult rollbacks, or deployment anxiety.
- `revert` commits paired with a follow-up `fix` a day later is the classic "shipped broken, reverted, re-shipped" loop — pay attention to the file involved.

---

## Cross-referencing — where the real signal is

A single command's output is interesting. The **intersection** is actionable:

| Combination | What it means |
|---|---|
| High churn (1) + high bug count (3) | Highest-risk code in the repo. Read this first. |
| High churn (1) + single owner (2) | Refactor blocker — only one person knows it. |
| Declining momentum (4) + missing architects (2) | Project is in maintenance mode or drifting. |
| Frequent crises (5) + churn on same files (1) | Deploy-fear hotspots — invest in tests/observability here. |
| Steady momentum (4) + low crisis count (5) + broad contributor base (2) | Healthy project. Read normally. |

---

## Reporting the results

When summarizing for a human (or for yourself before diving in), structure the takeaway as:

1. **Health snapshot** — momentum trend, contributor breadth, crisis frequency (one sentence each).
2. **Top 3 files to read first** — drawn from the churn ∩ bugs intersection.
3. **Top 3 risks** — bus factor, dying momentum, deploy anxiety, etc., with the evidence (numbers) attached.

Then, and only then, open the code.

---

## Caveats

- **Squash-merge repos** collapse history; per-file churn still works but contributor counts under-represent reviewers and pairing partners.
- **Monorepos** need per-package scoping — re-run inside each package directory.
- **Renamed files** split across two paths in `git log --name-only`. Add `--follow` when investigating a specific file, but it doesn't compose with the aggregation pipelines above.
- **Generated files** (lockfiles, migrations, snapshots) will dominate unless filtered. Always sanity-check the top of the churn list.
- **Commit message conventions vary.** Adjust the regex in commands 3 and 5 to match the team's vocabulary (e.g. Conventional Commits use `fix:`, `revert:` prefixes).
