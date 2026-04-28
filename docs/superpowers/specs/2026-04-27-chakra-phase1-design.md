# Chakra Phase 1 — Agentic SDLC Loop Design

**Date:** 2026-04-27  
**Scope:** Single user, no multi-tenancy. Story in → GitHub PR out.

---

## Overview

Chakra is a CLI tool that takes a plain-text user story (`story.txt`) and autonomously plans, codes, tests, and opens a GitHub PR — with one human approval gate after planning and full human review via the PR itself.

---

## Stack

| Concern | Library |
|---------|---------|
| LLM calls | `anthropic` SDK (Python 3.12) |
| GitHub operations | `PyGithub` |
| Google Sheets tracker | `gspread` + `google-auth` |
| Config | `PyYAML` |

Entry point: `python orchestrator.py story.txt`

---

## File Structure

```
chakra/
├── CLAUDE.md
├── chakra.yaml
├── orchestrator.py
├── agents/
│   └── sdlc_agent.py
├── tools/
│   ├── github_tool.py
│   ├── sheets_tool.py
│   └── approval_tool.py
├── credentials.json          # Google service account key (git-ignored)
└── requirements.txt
```

---

## Configuration — `chakra.yaml`

```yaml
github:
  repo: "owner/repo-name"
  base_branch: "main"
  ci_workflow: "ci.yml"

anthropic:
  model: "claude-opus-4-7"

google:
  credentials_path: "./credentials.json"
  spreadsheet_id: "your-sheet-id-here"

tracker:
  sheet_name: "Chakra Tracker"

story:
  id_prefix: "CHAKRA"
```

---

## Loop Flow

```
python orchestrator.py story.txt
        │
        ▼
1.  Load chakra.yaml, read story.txt
2.  Auto-assign Story ID (CHAKRA-001, CHAKRA-002, …)
3.  Sheets: upsert row, status = "Pending"
        │
        ▼
4.  SDLCAgent.plan(story) → list of tasks [{task, description}]
5.  Sheets: status = "Planning"
6.  approval_tool: print plan, prompt [y/n]     ← only human gate
        │ approved (max 3 retries with rejection feedback)
        ▼
7.  SDLCAgent.code(story, tasks) → {filename: content}
8.  Sheets: status = "Coding"
        │
        ▼
9.  SDLCAgent.test(story, code) → {filename: content}
10. Sheets: status = "Testing"
        │
        ▼
11. github_tool: create branch, commit code + tests, open PR
12. Sheets: status = "PR Created"
13. github_tool.poll_merge() — checks every 30s
        │ PR merged
        ▼
14. github_tool.trigger_cicd() — workflow_dispatch on ci_workflow
15. Sheets: status = "Done"
16. Print summary
```

**On planning rejection:** orchestrator re-invokes `plan()` with the rejection reason as additional context, re-prompts. After 3 failed retries, exits with error.

---

## Component Interfaces

### `agents/sdlc_agent.py`

```python
class SDLCAgent:
    def plan(self, story: str) -> list[dict]:
        # returns [{task: str, description: str}]

    def code(self, story: str, tasks: list[dict]) -> dict[str, str]:
        # returns {filename: file_content}

    def test(self, story: str, code: dict[str, str]) -> dict[str, str]:
        # returns {filename: test_content}
```

All methods call the Anthropic API with structured prompts. Responses are parsed from Claude's output (JSON mode or XML tags).

### `tools/github_tool.py`

```python
class GitHubTool:
    def create_branch(self, branch_name: str) -> None
    def commit_files(self, branch: str, files: dict[str, str], message: str) -> None
    def open_pr(self, branch: str, title: str, body: str) -> tuple[str, int]  # (pr_url, pr_number)
    def poll_merge(self, pr_number: int, interval_seconds: int = 30) -> None  # blocks
    def trigger_cicd(self, workflow: str, ref: str) -> None
```

### `tools/sheets_tool.py`

```python
class SheetsTool:
    def upsert_row(self, story_id: str, story_title: str, task: str, status: str) -> None
    def update_status(self, story_id: str, task: str, status: str) -> None
```

Columns: `Story ID | Story Title | Task | Status | Updated At`

### `tools/approval_tool.py`

```python
def prompt_approval(label: str, content: str) -> bool
# Prints label + content, prompts [y/n], returns True/False
# Raises ApprovalRejected(reason) when user types 'n' with optional reason
```

---

## Google Sheets Tracker

- Sheet is created/opened by name (`sheet_name` in config)
- One row per task per story
- Status values: `Pending` → `Planning` → `Coding` → `Testing` → `PR Created` → `Done`
- `Updated At` is a UTC timestamp, set on every status change

**Setup required (one-time):**
1. Create a Google Cloud project, enable Sheets API
2. Create a service account, download `credentials.json`
3. Share the target Google Sheet with the service account email

---

## GitHub Branch Naming

Branch: `chakra/{story-id}-{slugified-title}`  
Example: `chakra/CHAKRA-001-add-user-login`

---

## Error Handling

- `ApprovalRejected` — raised by `approval_tool`, caught in orchestrator, triggers retry loop
- GitHub API errors — bubble up with clear message, orchestrator exits non-zero
- Anthropic API errors — retried once with exponential backoff, then exit
- All status transitions in Sheets happen before the corresponding work starts, so a crash mid-step leaves an accurate last-known status

---

## Notifications (Phase 1)

Terminal only. The approval prompt in step 6 is the sole notification mechanism.  
Phase 2: replace with Gmail via SMTP or Gmail API.

---

## Logging

All SDLC lifecycle events are logged using Python's standard `logging` module at `DEBUG` level to a rotating file (`logs/chakra.log`) and at `INFO` level to stdout.

Logged at every step:
- Story ID, step name, timestamp on entry and exit
- Full Claude API prompt and response (DEBUG)
- GitHub operations: branch name, commit SHA, PR URL, merge detected
- Sheets updates: story ID, task, old status → new status
- Approval prompt: user input (y/n) and rejection reason if given
- Coverage report output and retry count
- Any exception with full traceback

**Log format:** `%(asctime)s [%(levelname)s] %(name)s — %(message)s`

A `logs/` directory is auto-created on first run. `logs/` is git-ignored.

File structure addition:
```
chakra/
└── logs/
    └── chakra.log    # rotating, max 10MB × 5 backups
```

---

## Test Coverage Requirement

`SDLCAgent.test()` must generate tests that achieve **≥ 95% line coverage** on the code it produces. The agent is prompted to write tests until coverage meets this threshold. Coverage is measured by running `pytest --cov` and parsing the output; if coverage is below 95%, the agent is re-invoked with the coverage report as feedback (max 3 retries, then exit with error).

The `ci.yml` workflow triggered on PR merge must also enforce the 95% threshold as a CI gate — the pipeline fails if coverage drops below 95%.

---

## Out of Scope for Phase 1

- Multi-tenancy
- Web UI
- Webhook-based PR merge detection (polling is used)
- Email notifications
- Resume after crash (stateless — restart from scratch)
