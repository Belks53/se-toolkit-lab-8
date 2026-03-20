# Lab 7 — Build a Client with an AI Coding Agent

## Concept

Students use an AI coding agent (Qwen Code) to build a Telegram bot client
for the LMS backend they deployed in Labs 5–6.

The lab teaches how to collaborate with an AI agent as a development partner:
plan, scaffold, build iteratively, debug with agent assistance, and deliver
a working product connected to a real backend.

## Prerequisites

- Labs 2–6 completed (backend deployed on VM with PostgreSQL, ETL, analytics)
- Student's LMS backend running on VM (port 42002 via Caddy)
- Working API key for the backend (`LMS_API_KEY`)
- Telegram bot token (from @BotFather)

> **Base repo:** Lab 7 forks from `se-toolkit-lab-7` (which is a copy of
> `se-toolkit-lab-6`). Students get the working backend + frontend + Docker
> Compose as their starting point. They add Telegram bot code into the
> same repo — not a separate project.

### SSH Setup (carried over from Lab 6 Task 3)

In Lab 6 Task 3, students added the autochecker SSH public key to their
**own user's** `~/.ssh/authorized_keys` and registered their `vm_username`
with the bot. Lab 7 relies on this same setup — the autochecker SSHes as
the student's main user for all runtime checks.

**Lab 7 setup must verify this is still in place.** If a student skipped
Lab 6 Task 3 or reinstalled their VM, they need to redo it:

```bash
# On their VM, as their main user:
mkdir -p ~/.ssh
echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKiL0DDQZw7L0Uf1c9cNlREY7IS6ZkIbGVWNsClqGNCZ se-toolkit-autochecker' >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys
```

The bot already stores `vm_username` from Lab 6. If missing, the lab setup
task should prompt the student to register it (same flow as Lab 6 Task 3:
run `whoami`, reply to the bot).

## Learning Outcomes

1. Use an AI coding agent to plan and implement a client application
2. Design a testable handler architecture (logic separated from transport)
3. Connect a client to an existing REST API with authentication
4. Debug integration issues iteratively with agent assistance
5. Deploy a multi-service system (backend + bot) on a remote VM

---

## Verification Model

> No `clone_and_run`. No separate `autochecker` SSH user.
> Two verification channels: **GitHub API** for code, **SSH** for deployment.
>
> **Structural checks → GitHub API**
> File existence, word counts, regex matches — same as Labs 1–6.
> We know the student's GitHub alias and repo name, so this works out of the box.
>
> **Runtime & deployment checks → SSH as student's main user**
> SSHes to the student's VM as their main user (`vm_username`).
> Runs `python bot.py --test`, `docker ps`, `curl`, etc.
> All checks see the real environment — real backend, real `.env`, real Docker.
>
> **Repo integrity check → SSH**
> Verify that the deployed code on the VM actually comes from the student's
> GitHub repo. SSH in, run `git -C <project-dir> remote get-url origin`,
> and confirm it matches `github.com/{alias}/{repo-name}`.
> This prevents students from deploying someone else's code.
>
> **Implications:**
> - `--test` mode hits the **real backend on localhost** — no mock client needed
> - If the backend is down, `/health` should report it as down (correct behavior)
> - Student must have their repo cloned and their code deployed on the VM
>
> **Project directory discovery:** Autochecker looks for `~/lab-07-*` or the
> repo name from the spec. Fallback: search home dir for `bot.py`/`main.py`.

---

## Prioritized Requirements

### P0 — Must Have

1. Project builds and starts without errors
2. Testable handler layer — handlers callable without Telegram
3. CLI test mode: `python bot.py --test "/command"` prints response to stdout
4. `/start` — welcome message with bot description
5. `/help` — lists all available commands with descriptions
6. `/health` — calls backend `GET /items`, reports up/down status
7. At least 2 data commands that fetch real data from the LMS backend
8. README with: what the bot does, how to install, how to configure, how to run

### P1 — Should Have

1. Natural language intent routing — plain text messages (no `/` prefix)
   are interpreted by an LLM that picks the right tools/actions
2. Inline keyboard buttons or reply menu for main commands
3. Periodic health check (configurable interval, logs or sends alert on failure)
4. Graceful error handling (backend down → user-friendly message, not crash)

### P2 — Nice to Have

1. Rich message formatting (tables, charts as images)
2. Multi-step reasoning (bot chains multiple API calls to answer one question)
3. Response caching for expensive queries
4. Conversation context (multi-turn)

---

## Task Breakdown

### Setup

**Goal:** Ensure the student's VM is reachable, the repo is forked, the
backend is deployed and running, and the database has data (ETL synced).
Mirrors Lab 6 setup checks + deployment + sync.

**What students do:**
1. Fork the lab-7 template repo on GitHub, enable Issues
2. Ensure SSH key is in `~/.ssh/authorized_keys` (from Lab 6 Task 3)
3. Register `vm_username` with the bot (if not already done)
4. Stop Lab 6 containers (`docker compose --env-file .env.docker.secret down`)
5. Clone the repo on their VM
6. Copy `.env.docker.example` → `.env.docker.secret`, fill in credentials
7. Configure Docker DNS on VM (`dns: ["8.8.8.8", "8.8.4.4"]` in daemon.json)
8. Run `docker compose --env-file .env.docker.secret up --build -d`
9. Trigger ETL sync: `curl -X POST http://localhost:42002/pipeline/sync`
   (populates database — without this, all analytics return empty)
10. Verify dashboard shows data at `http://VM_IP:42002`
11. Get a Telegram bot token from @BotFather

> Setup instructions are implemented in `lab/setup/setup-simple.md`.

**Auto-checks (reused from Lab 6):**

| ID | Check | Channel | How |
|----|-------|---------|-----|
| setup-repo | Repository exists on GitHub | GitHub | `repo_exists` |
| setup-fork | Repository is a fork of the template | GitHub | `repo_is_fork` |
| setup-issues | GitHub Issues are enabled | GitHub | `repo_has_issues` |
| setup-ssh | SSH connectivity as student's main user | SSH | `ssh_check` — `echo ok` as `vm_username` |
| setup-backend | LMS backend is running | SSH | `ssh_check` — `curl -sf http://localhost:42002/docs` returns 200 |
| setup-data | Database has data (ETL was synced) | SSH | `ssh_check` — `curl -sf -H 'Authorization: Bearer <key>' http://localhost:42002/items/` returns non-empty JSON array |

> Setup checks are mostly identical to Lab 6. The new check (`setup-data`)
> verifies the student ran the ETL sync. Without it, the bot's data
> commands and intent routing will return empty results.

### Task 1 — Plan and Scaffold

**Goal:** Use Qwen Code to create a development plan and project skeleton.

**What students do:**
1. Give the prioritized requirements to Qwen Code
2. Ask it to produce an implementation plan
3. Ask it to scaffold the project
4. Verify the scaffold runs

**Deliverables:**
- `bot/PLAN.md` — development plan produced with agent assistance
- Bot code in a `bot/` directory with separated handler layer
- Bot dependencies in `bot/pyproject.toml` (managed with `uv sync`)
- `BOT_TOKEN` added to `.env.bot.example`
- Bot entry point (`bot/bot.py` or `bot/main.py`) that starts without crashing
- CLI test mode wired up (even if handlers return placeholder text)

> Students add their bot code inside the existing repo (forked from lab-7
> template). The repo already has `backend/`, `frontend/`, `docker-compose.yml`,
> `README.md`, etc. The bot lives in a `bot/` subdirectory.

**Auto-checks:**

| ID | Check | Channel | How |
|----|-------|---------|-----|
| t1-plan | `bot/PLAN.md` exists and has ≥100 words | GitHub | file_exists + file_word_count |
| t1-env | `.env.bot.example` contains `BOT_TOKEN` | GitHub | regex_in_file |
| t1-deps | `bot/pyproject.toml` exists | GitHub | file_exists |
| t1-handlers | Handler directory exists | GitHub | file_exists — `bot/handlers/` |
| t1-install | Bot dependencies install without errors | SSH | `cd bot && uv sync` on VM |
| t1-test-mode | `cd bot && uv run bot.py --test "/start"` exits 0 and produces output | SSH | check exit code + stdout non-empty |
| t1-env-vm | `.env.bot.secret` exists on VM | SSH | `test -f ~/se-toolkit-lab-7/.env.bot.secret` |

### Task 2 — Backend Integration

**Goal:** Connect the bot to the student's LMS backend with real data commands.

**What students do:**
1. Implement `/health` that calls `GET /items` on their backend
2. Implement `/labs` and `/scores <lab>` data commands
3. Handle backend errors gracefully
4. Test locally, then against their deployed backend
5. Deploy and verify in Telegram

**Required data commands:**

| Command | Backend endpoint | What it shows |
|---------|-----------------|---------------|
| `/labs` | `GET /items` | List of available labs |
| `/scores <lab>` | `GET /analytics/pass-rates?lab=` | Per-task pass rates |
| `/timeline <lab>` | `GET /analytics/timeline?lab=` | Submissions over time |
| `/groups <lab>` | `GET /analytics/groups?lab=` | Per-group performance |
| `/top [lab] [N]` | `GET /analytics/top-learners?lab=&limit=` | Top N learners |
| `/learners` | `GET /learners` | Enrolled learner count/list |
| `/sync` | `POST /pipeline/sync` | Trigger ETL, show result |

**Auto-checks:**

| ID | Check | Channel | How |
|----|-------|---------|-----|
| t2-start | `--test "/start"` returns text containing "welcome" or bot name (case-insensitive) | SSH | regex on stdout |
| t2-help | `--test "/help"` output lists at least 4 commands | SSH | count `/command` patterns in stdout |
| t2-health | `--test "/health"` output contains "healthy" or "ok" or status indicator | SSH | hits real backend on localhost |
| t2-labs | `--test "/labs"` returns non-empty structured output | SSH | stdout has ≥2 lines |
| t2-scores | `--test "/scores lab-04"` returns task names and scores | SSH | stdout non-empty, ≥2 lines |
| t2-error | Backend error produces user-friendly message, not traceback | SSH | stop backend → `--test "/health"` → no `Traceback` → restart |

> `--test` mode hits the real backend on localhost. No mock needed.

### Task 3 — Intent-Based Natural Language Routing

**Goal:** The bot accepts plain text messages (no `/` prefix needed) and
uses an LLM to determine the user's intent, pick the right backend tools,
and compose a response. This is a mini-agent inside the bot.

**What students do:**
1. Define available "tools" — backend API endpoints the LLM can call
2. Implement an intent router: user message → LLM decides which tools
   to call → fetches data → formats response
3. Add inline keyboard buttons or a reply keyboard for common actions
4. Handle ambiguous and invalid inputs gracefully

**How it works:**
```
User: "which lab has the worst results?"
Bot:  → sends message + tool definitions to LLM
      → LLM decides: call GET /analytics/pass-rates for each lab
      → bot executes the API calls
      → LLM summarizes: "Lab 3 has the lowest average at 62%..."
      → bot sends formatted response
```

This directly builds on Lab 6 (tool use / function calling) — students
reuse the pattern of giving an LLM a set of tools and letting it decide
which to call. The difference: in Lab 6 they built the agent, here the
agent is embedded inside a user-facing product.

**Scenarios to cover:**

*Direct data queries (single API call):*

| User message | Intent | Tool |
|---|---|---|
| "what labs are available?" | list items | `GET /items` |
| "how many students are enrolled?" | learner count | `GET /learners` |
| "show me scores for lab 4" | score distribution | `GET /analytics/scores?lab=lab-04` |
| "who are the top 5 students?" | leaderboard | `GET /analytics/top-learners?limit=5` |
| "which group is doing best in lab 3?" | group comparison | `GET /analytics/groups?lab=lab-03` |

*Multi-step reasoning (multiple API calls):*

| User message | Intent | Tools |
|---|---|---|
| "which lab has the lowest pass rate?" | compare across labs | `GET /items` → `GET /analytics/pass-rates` per lab → compare |
| "is the class improving over time?" | trend analysis | `GET /analytics/timeline` for recent labs → compare |
| "compare group A and group B" | group diff | `GET /analytics/groups` → filter → compare |

*System / meta:*

| User message | Intent | Action |
|---|---|---|
| "is the backend running?" | health check | `GET /items` → 200 = ok |
| "sync latest data" | trigger ETL | `POST /pipeline/sync` |
| "what can you do?" | capabilities | No API call — list what bot can do |

*Fallback / ambiguous:*

| User message | Intent | Action |
|---|---|---|
| "hello" | greeting | Friendly response + hint about capabilities |
| "lab 4" | ambiguous | Clarify: "What about lab 4? I can show scores, pass rates..." |
| "asdfgh" | nonsense | "I didn't understand. Here's what I can help with..." |

**Auto-checks:**

| ID | Check | Channel | How |
|----|-------|---------|-----|
| t3-intent | `--test "what labs are available"` (no `/` prefix) returns non-empty answer (≥20 chars) | SSH | real LLM key + real backend |
| t3-multi | `--test "which lab has the lowest pass rate"` returns answer mentioning a lab name | SSH | regex for `lab-\d+` or lab title in stdout |
| t3-fallback | `--test "asdfgh"` returns a helpful message, not a crash or empty response | SSH | stdout non-empty, no `Traceback` |
| t3-buttons | Source code contains keyboard/button setup | GitHub | regex_in_file — `InlineKeyboardMarkup\|ReplyKeyboardMarkup` or equivalent |
| t3-tools | Source code defines at least 9 tool/function schemas | GitHub | regex_in_file — count occurrences of `"type": "function"` or `"name":` patterns in tool definitions, ≥9 matches |

> Intent-based checks run with the student's own `.env` on their VM
> (real LLM key + real backend). If the key is missing, check fails.

### Task 4 — Containerize and Document

**Goal:** Containerize the bot (move from `nohup` to Docker) and document deployment.

**What students do:**
1. Create `bot/Dockerfile`
2. Add bot service to `docker-compose.yml`
3. Handle Docker networking (backend via service name, qwen proxy via `host.docker.internal`)
4. Verify bot works from container in Telegram
5. Update README with deployment instructions

**Auto-checks:**

| ID | Check | Channel | How |
|----|-------|---------|-----|
| t4-dockerfile | `bot/Dockerfile` exists | GitHub | file_exists |
| t4-repo-match | Deployed code is from student's GitHub repo | SSH | `git remote get-url origin` matches `github.com/{alias}/{repo}` |
| t4-compose | `docker-compose.yml` includes a bot service | SSH | `grep -i bot docker-compose.yml` |
| t4-running | Bot container is running | SSH | `docker ps` shows bot container |
| t4-health | Backend is still up alongside the bot | SSH | `curl -sf http://localhost:42002/docs` returns 200 |
| t4-readme | README has "deploy" or "containerize" section | GitHub | regex_in_file — heading containing "deploy" or "containerize" |

**TA verification (demo):**
- Bot responds to `/start`, `/help`, `/health` in Telegram
- At least 2 data commands return real backend data
- Plain text questions get routed correctly (intent detection works)
- Multi-step query produces a coherent answer
- Student explains how they used Qwen Code during development
- Student can explain the handler + intent routing architecture

---

## Verification Strategy

### Auto-Checked (autochecker)

**GitHub API** — structural checks on the repo (file existence, content, regex):

**SSH as student's main user** — runtime & deployment checks on the VM:

**Setup (6 checks) — reused from Lab 6 + data check**
- GitHub: repo exists, is fork, issues enabled
- SSH: connectivity, backend running, database has data (ETL synced)

**Task 1 — Structure & Scaffold (7 checks)**
- GitHub: bot/PLAN.md, .env.bot.example, bot/pyproject.toml, bot/handlers/
- SSH: dependencies install, `--test "/start"` works, .env.bot.secret exists

**Task 2 — Backend Integration (6 checks)**
- SSH: /start, /help return expected content via test mode
- SSH: /health returns status (real backend on localhost)
- SSH: /labs and /scores return real data
- SSH: error handling (no traceback on failure)

**Task 3 — Intent Routing (5 checks)**
- SSH: plain text query returns answer, multi-step query works, fallback works
- GitHub: button/keyboard code exists, ≥9 tool schemas defined

**Task 4 — Containerize & Document (6 checks)**
- GitHub: bot/Dockerfile exists, README has deploy section
- SSH: repo integrity, compose has bot service, bot container running, backend healthy

**Total: ~30 auto-checks (6 setup + 7 + 6 + 5 + 6)**

### TA-Verified (demo)

- Live Telegram interaction
- Real backend data flowing through bot
- Plain text intent routing quality and relevance
- Multi-step reasoning demo (e.g., "which lab has the lowest pass rate?")
- Code walkthrough: handler + intent routing architecture
- Development process: how Qwen Code was used
- Interaction quality and usability

---

## Test Mode Specification

The bot must support a `--test` flag for offline command verification:

```bash
# Syntax (run from repo root)
cd bot && uv run bot.py --test "<message>"

# Slash commands
cd bot && uv run bot.py --test "/start"
cd bot && uv run bot.py --test "/help"
cd bot && uv run bot.py --test "/health"
cd bot && uv run bot.py --test "/labs"

# Natural language (intent routing)
cd bot && uv run bot.py --test "what labs are available"
cd bot && uv run bot.py --test "which lab has the lowest pass rate"
cd bot && uv run bot.py --test "asdfgh"
```

**Behavior:**
- Prints the bot's response text to **stdout**
- Hits the **real backend on localhost:42002** (reads config from `.env.bot.secret`)
- Exits with code **0** on success, **non-zero** on error
- Does NOT connect to Telegram (no `BOT_TOKEN` required in test mode)
- LLM-dependent messages use the real LLM key from `.env.bot.secret`
- Messages without `/` prefix go through the intent router (Task 3)

**Why this matters:**
- Autochecker can verify handler logic without Telegram
- Forces students to separate handlers from transport (good architecture)
- Makes development faster (test without deploying to Telegram)

**Implementation hint for students:**

```python
# bot/bot.py (simplified)
import sys
from handlers import handle_command
from services.api_client import ApiClient

if __name__ == "__main__":
    if "--test" in sys.argv:
        command = sys.argv[sys.argv.index("--test") + 1]
        client = ApiClient()  # reads backend URL from .env.bot.secret
        print(handle_command(command, client))
    else:
        # normal Telegram bot startup
        ...
```

---

## Architecture Guidance (given to students)

```
se-toolkit-lab-7/           ← forked repo (already has backend/, frontend/, etc.)
├── bot/                    ← NEW — all bot code goes here
│   ├── bot.py              ← entry point (Telegram startup OR --test mode)
│   ├── handlers/
│   │   ├── commands.py     ← /start, /help, /health, /labs, etc.
│   │   └── intent.py       ← natural language router (LLM picks tools)
│   ├── tools/
│   │   ├── api.py          ← tool definitions for LLM (get_items, get_scores, etc.)
│   │   └── registry.py     ← tool registry mapping names → functions
│   ├── services/
│   │   ├── api_client.py   ← HTTP client for LMS backend
│   │   └── llm.py          ← LLM integration (OpenRouter/Qwen)
│   ├── config.py           ← env var loading
│   ├── pyproject.toml      ← bot-specific dependencies (uv sync)
│   ├── Dockerfile          ← bot container
│   └── PLAN.md             ← development plan from Qwen Code
├── backend/                ← existing (from lab-6 fork)
├── frontend/               ← existing
├── docker-compose.yml      ← existing — students ADD a bot service
├── .env.bot.example      ← existing — students ADD BOT_TOKEN
└── .env.docker.secret      ← existing — backend credentials
```

Students don't have to follow this exactly — it's a suggestion. The key
requirements are:
- Handlers testable without Telegram (via `--test` mode)
- Intent router uses tool/function definitions the LLM can choose from
- Slash commands and plain text both work

---

## Scoring

| Task | Weight | Notes |
|------|--------|-------|
| Task 1 — Plan & Scaffold | 20% | Mostly structural checks |
| Task 2 — Backend Integration | 30% | Core functionality |
| Task 3 — Intent Routing | 30% | LLM tool use + natural language |
| Task 4 — Containerize & Document | 20% | Dockerfile + Docker Compose + README |

Pass threshold: 75% (consistent with other labs)

---

## Reuse from Lab 6

Lab 7 forks `se-toolkit-lab-6`. Here's what carries over and what changes.

**Reused as-is (check types + engine methods):**
- `repo_exists`, `repo_is_fork`, `repo_has_issues` — standard GitHub checks
- `ssh_check` — SSH connectivity and command execution via `vm_username`
  (routes internal 10.x IPs through relay, public IPs direct)
- `glob_exists` — file pattern matching on GitHub
- `regex_in_file` — code pattern validation on GitHub
- `file_word_count`, `file_nonempty` — content checks on GitHub
- Scoring config: `mode: weighted`, `pass_threshold: 0.75`, `score_required_only: true`
- Task prerequisites: all tasks depend on `setup`
- `depends_on` between checks (e.g., `backend_running` depends on `ssh_connectivity`)

**Reused with modifications:**
- `backend_running` — same `ssh_check` type, update port to 42002 and path to `/docs`
- `.env.example` regex check — different env vars: `BOT_TOKEN`, `LMS_API_URL`,
  `LMS_API_KEY`, `LLM_API_KEY` (same as Lab 6, plus `BOT_TOKEN`)
- `glob_exists` for required files — different file list (PLAN.md, handlers/,
  bot.py vs Lab 6's agent.py, AGENT.md)

**Not reused (Lab 6 specific):**
- `agent_eval` check type (Docker sandbox eval with question bank)
- `issue_pr_approved` (PR approval workflow — TBD for Lab 7)
- `clone_and_run` (replaced by SSH-only checks)
- `task1_reads_env_vars` checking for `LLM_API_KEY` in `agent.py`
- `task2_agent_tools` checking for `read_file`/`list_files`

**New for Lab 7:**
- SSH-based `--test` command execution (run `python bot.py --test "..."`,
  check stdout) — uses `ssh_check` with custom commands
- Repo integrity check (`git remote get-url origin` via SSH)
- Intent routing checks (plain text → LLM → tool calls → response)

---

## Open Questions

1. **Periodic health check verification:**
   - Hard to auto-check a background task
   - Could require a `--test-healthcheck` flag that runs one cycle and exits
   - **Leaning toward:** P1 (should have), TA-verified in demo

2. **Eval set for Task 3 intent routing:**
   - Current t3 checks only verify output shape (non-empty, mentions a lab name) — passable with regex routing that bypasses the LLM entirely
   - Lab 6 had `agent_eval` (Docker sandbox + question bank) — the idea was valid but the sandbox caused debugging pain
   - Simpler approach for Lab 7: define a bank of `--test "..."` queries with expected output patterns, run via SSH exactly like existing checks, no sandbox needed
   - Queries must be designed so regex cannot satisfy them — e.g. semantic reasoning required: "which lab covers Docker?" (requires knowing lab content), "how does lab 3 compare to lab 4 in pass rate?" (requires two API calls + comparison)
   - Could also include a negative check: source code must not contain `re.search` or `re.match` in the intent routing path
   - **Leaning toward:** add 2–3 eval queries to t3 auto-checks in next iteration; keep queries in a versioned file so they can be updated without changing the spec

## Resolved Decisions

- **Base repo:** Fork from `se-toolkit-lab-7` (copied from lab-6). Students
  get working backend + frontend + Docker Compose. Bot code goes in `bot/`
  subdirectory within the same repo.
- **Setup:** Implemented in `lab/setup/setup-simple.md`. Includes: stop Lab 6
  containers, configure Docker DNS, deploy, ETL sync, SSH key, bot token.
- **Setup checks:** Reuse Lab 6's `repo_exists`, `repo_is_fork`,
  `repo_has_issues`, `ssh_check`, `backend_running` + new `setup-data`.
- **Verification model:** GitHub API for structural checks, SSH for runtime.
  No `clone_and_run`. No `autochecker` SSH user.
- **SSH user:** Always SSH as the student's main user (`vm_username`).
  This gives access to repo, Docker, `.env`, everything.
- **Repo integrity:** `git remote get-url origin` on VM must match the
  student's known GitHub alias + repo name.
- **Mock client:** Not needed. `--test` mode hits the real backend on localhost.
- **Env vars:** Bot-specific vars (`BOT_TOKEN`) go in `.env.bot.secret`
  (already gitignored via `*.secret`). Backend vars stay in `.env.docker.secret`.
- **LLM API key:** Runs with student's own `.env.bot.secret` on their VM.
  If key is missing, check fails — student's responsibility.
- **Docker network:** Single compose file with bot + backend on the same
  network. Bot reaches backend via Docker service name.
- **Project directory:** `~/se-toolkit-lab-7`. Bot code in `bot/` subdirectory.
- **ETL score bug:** API returns null scores for ~93% of records. Fixed in ETL
  by computing `score = (passed / total) * 100` when API score is null.
- **Docker DNS:** University VMs can't resolve `registry.npmjs.org`. Setup
  instructions include `daemon.json` DNS fix as an explicit step.
- **Registry prefix:** `REGISTRY_PREFIX` build arg — defaults to university
  harbor cache, set empty for Docker Hub outside campus.
