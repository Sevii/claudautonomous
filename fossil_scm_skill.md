---
name: fossil-scm-cli
description: Practical CLI guide for the Fossil SCM (https://fossil-scm.org). Use when coding against a Fossil-tracked project (clone, commit, branch, merge, sync) or when triaging/reviewing the integrated tickets, timeline, and tasks via the `fossil` command line.
---

# Fossil SCM — Command-Line Skill Guide

Fossil is a distributed SCM that bundles version control, bug tracking, wiki, forum, and chat in a **single self-contained `fossil` binary** and a single `*.fossil` SQLite repository file. This guide is task-oriented: how to code in a Fossil checkout, and how to review/manage tickets and tasks from the CLI.

Reference: <https://fossil-scm.org/home/doc/trunk/www/index.wiki>

---

## 1. Mental model (read this first)

| Concept | Meaning |
|---|---|
| **Repository** | A single `something.fossil` file (a SQLite DB). Holds *all* history, tickets, wiki, forum. |
| **Check-out** | A working directory linked to one repository file via `fossil open`. |
| **Check-in / artifact** | A commit. Identified by a SHA1/SHA3-256 hash. Artifacts are individual file blobs. |
| **Leaf** | A check-in with no children — i.e. the tip of some line of development. |
| **Branch** | A *named*, intentional fork. The default branch is `trunk` (not `main`/`master`). |
| **Autosync** | On by default: most commands push/pull automatically against the parent repo. You usually do **not** need explicit `push`/`pull`. |
| **Ticket** | A row in the repo's ticket table — Fossil's built-in issue tracker. Each has a UUID. |

If you've used Git: a `.fossil` file replaces `.git/`, `trunk` replaces `main`, and `fossil ui` replaces a separate forge.

---

## 2. Repository setup

```bash
# Brand-new project
fossil init project.fossil
fossil open  project.fossil

# Cloning an existing remote
fossil clone https://example.org/repo  myrepo.fossil
fossil clone https://user@example.org/repo myrepo.fossil   # with auth

# Open a checkout in the current dir (use --force if dir is non-empty)
fossil open myrepo.fossil
fossil open myrepo.fossil --force

# Inspect the link between checkout and repo
fossil info
fossil status         # also shows current branch, parent, changes
```

Tip: keep `*.fossil` files **outside** their checkouts (e.g. `~/fossils/foo.fossil`). The checkout only needs the link Fossil creates on `open`.

---

## 3. Coding workflow

### 3.1 Find your bearings

```bash
fossil status                # branch, parent check-in, changed files
fossil changes               # just the file change list
fossil timeline -n 20        # last 20 events on current branch
fossil timeline -n 20 -t ci  # check-ins only (filter by type)
fossil branch list           # all branches; current marked with *
fossil info <hash>           # details about a check-in or artifact
```

### 3.2 Edit, stage, commit

Fossil tracks files explicitly — new files must be `add`ed. There is no staging area separate from the working tree; `commit` snapshots the whole checkout.

```bash
fossil add path/to/new_file.py
fossil rm  path/to/old_file.py        # also deletes from disk; use --soft to keep
fossil mv  src.py dst.py              # rename (tracked); --soft to leave disk alone
fossil addremove                      # auto-add new + auto-remove missing
fossil clean -n                       # dry-run: list untracked junk
fossil clean --verily                 # actually delete (destructive — confirm with user)

fossil diff                           # unstaged diff
fossil diff --from <hash> --to <hash>
fossil diff -v file.py                # one file

fossil commit -m "Concise summary"
fossil commit                          # opens $EDITOR for the message
fossil commit --no-warnings -m "..."  # skip CR/LF, encoding, etc. warnings
```

Commit messages: first line = subject, blank line, then body. Reference tickets by hash prefix (`See [abc1234]`) — Fossil auto-links.

### 3.3 Branching and merging

```bash
# Create a branch *as you commit* (preferred)
fossil commit --branch feature/login -m "Start login work"

# Switch to an existing branch
fossil update trunk
fossil update feature/login

# Merge another branch into the current checkout
fossil update trunk                    # be on the destination
fossil merge feature/login
fossil commit -m "Merge feature/login"

# Useful merge variants
fossil merge --cherrypick <hash>       # single check-in
fossil merge --backout    <hash>       # reverse a check-in
fossil merge --integrate  feature/x    # close the source branch on commit
```

Forks (accidental sibling leaves on the same branch) show up in `fossil leaves` and `fossil status`. Resolve by `fossil update` to one tip and `fossil merge` the other.

### 3.4 Stashing and undoing

```bash
fossil stash save -m "WIP: refactor"
fossil stash list
fossil stash show  N
fossil stash pop  N
fossil stash drop N

fossil revert path/to/file.py          # discard local edits to one file
fossil revert                          # discard all local edits (confirm first!)
fossil undo                            # reverse the *last* fossil command that changed the checkout
```

`fossil undo` is local and only undoes the most recent destructive checkout-side command (e.g. an `update`, `merge`, `revert`). It does **not** undo a pushed commit.

### 3.5 Sync with the remote

Autosync is on by default, so `commit`, `update`, and `merge` already talk to the server. Manual controls:

```bash
fossil remote                          # show configured remote URL(s)
fossil remote add  origin https://...  # add another
fossil pull
fossil push
fossil sync                            # bidirectional
fossil settings autosync off           # disable autosync (per checkout)
```

### 3.6 Tags, releases, and the web UI

```bash
fossil tag add release-1.2 trunk
fossil tag list
fossil ui                              # opens repo browser on http://localhost:8080
fossil ui --port 9000 path/to/repo.fossil
```

`fossil ui` is the fastest way to inspect a check-in graph, diffs, tickets, and the forum locally.

---

## 4. Reviewing tickets and tasks

Tickets in Fossil are issue-tracker entries stored in the same `.fossil` file. Each has a UUID (full hash) but you can use any unambiguous prefix.

### 4.1 Browse and search

```bash
fossil ticket list reports             # available report views
fossil ticket list fields              # ticket schema (columns)

# Run a report by name or number; output is TAB-separated
fossil ticket show "Active Tickets"
fossil ticket show 1
fossil ticket show 1 "status='Open' AND priority<=3"
fossil ticket show 1 --limit 20

fossil search "login bug"              # full-text search across tickets, wiki, check-ins
```

For browsing visually, `fossil ui` → **Tickets** tab gives filters, custom reports, and edit forms backed by the same data.

### 4.2 Inspect a single ticket

```bash
fossil ticket history <UUID-or-prefix>   # every change applied, oldest first
```

To dump current field values, run a report filtered to that UUID, e.g.:

```bash
fossil ticket show "All Tickets" "tkt_uuid GLOB 'abc123*'"
```

### 4.3 Create, edit, comment

```bash
# New ticket — pass FIELD VALUE pairs
fossil ticket add \
  title    "Login fails on Safari 17" \
  type     "Code_Defect" \
  status   "Open" \
  severity "Important" \
  comment  "Repro: open /login in Safari → blank page; works in Firefox."

# Update a ticket (set or change are aliases)
fossil ticket set    <UUID> status   "Review"
fossil ticket change <UUID> priority 2 comment "Patch in branch fix/login-safari"

# Multiline / special chars: use --quote and \n, \t, \s for newline/tab/space
fossil ticket add --quote \
  title   "Crash\son\sstartup" \
  comment "Stacktrace:\n\sat\sfoo()\n\sat\sbar()"

# Append (instead of overwrite) by prefixing the field name with +
fossil ticket change <UUID> +comment "Reproduced on macOS 14 too."
```

### 4.4 Tying check-ins to tickets

There is no automatic "fixes #N" syntax, but Fossil hyperlinks bracketed hashes anywhere it renders Markdown/wiki. Conventions:

- Put the ticket UUID prefix in the commit message: `Fixes [abc1234]: login crash on Safari`.
- After committing, append a comment to the ticket pointing at the check-in:
  ```bash
  fossil ticket change abc1234 \
    status   "Fixed" \
    +comment "Resolved in check-in [$(fossil info | awk '/^checkout:/ {print substr($2,1,10)}')]"
  ```

### 4.5 Task / review checklist (recommended sequence)

When asked to "review tickets" or triage tasks, walk this loop:

1. `fossil pull` — make sure you have the latest ticket state.
2. `fossil ticket show "Active Tickets"` (or your team's report) to get the queue.
3. For each candidate UUID:
   - `fossil ticket history <uuid>` — read the full thread.
   - `fossil timeline -p <uuid>` and `fossil search <keywords>` — find related check-ins.
   - Decide: needs info / reproducible / ready to fix / duplicate / wontfix.
   - Update with `fossil ticket change …` (status, priority, +comment).
4. If you start work, branch with `fossil commit --branch fix/<short-slug>` and reference the UUID in the message.
5. On fix, set the ticket to `Fixed`/`Closed` and link the resolving check-in hash.

---

## 5. Configuration knobs you'll actually use

```bash
fossil settings                         # list everything (current + default)
fossil settings autosync off            # local: don't auto-push on commit
fossil user default                     # who you are
fossil user new alice                   # add a user (admin-only on server)
fossil user capabilities alice          # check perms (tickets, wiki, push…)
fossil set editor "code -w"             # editor for commit messages
fossil set ui-width 132                 # preferred diff width
```

Per-checkout settings are stored in the checkout's `_FOSSIL_` file; global defaults in `~/.fossil`.

---

## 6. Quick reference card

| Task | Command |
|---|---|
| Status | `fossil status` |
| Recent history | `fossil timeline -n 20` |
| Diff working tree | `fossil diff` |
| Add new file | `fossil add FILE` |
| Commit | `fossil commit -m "msg"` |
| New branch + commit | `fossil commit --branch NAME -m "msg"` |
| Switch branch | `fossil update NAME` |
| Merge | `fossil merge NAME` then `fossil commit` |
| Stash | `fossil stash save -m "msg"` / `fossil stash pop N` |
| Undo last local op | `fossil undo` |
| Sync | `fossil sync` (or rely on autosync) |
| Local web UI | `fossil ui` |
| List tickets | `fossil ticket show "Active Tickets"` |
| Show one ticket | `fossil ticket history UUID` |
| New ticket | `fossil ticket add FIELD VALUE …` |
| Update ticket | `fossil ticket change UUID FIELD VALUE …` |
| Search everything | `fossil search "phrase"` |

---

## 7. Gotchas

- **`trunk`, not `main`.** Most defaults assume the branch name `trunk`.
- **Autosync surprises.** A `commit` may push immediately; if you're working offline or on sensitive history, `fossil settings autosync off` first.
- **`fossil clean --verily` is destructive.** It deletes untracked files outright — confirm before running.
- **Ticket field names vary by repo.** `fossil ticket list fields` first; the schema is per-repo configurable via `tktsetup`.
- **No staging area.** `commit` always captures the whole checkout. Use `fossil commit FILE…` to limit scope to specific paths.
- **`fossil undo` only steps back one command** and only on the local checkout. Pushed commits live on; use `fossil merge --backout <hash>` to reverse them publicly.
- **Hash prefixes** work everywhere a UUID is accepted, as long as they're unambiguous.

---

## 8. When to reach for `fossil ui`

Use the CLI for scripted/automated work and for fast inspection. Use `fossil ui` (or the remote web UI) for: configuring ticket reports, designing custom report SQL, editing wiki pages, reviewing forum threads, or visually inspecting the check-in DAG. They share the same SQLite store, so changes from either side are equivalent.
