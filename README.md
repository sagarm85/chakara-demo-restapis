# Chakra

Agentic SDLC loop: drop in a user story, get a GitHub PR — autonomously planned, coded, and tested by Claude.

```
python3 orchestrator.py story.txt
```

---

## How It Works

1. Reads `story.txt` (plain text user story, first line used as title)
2. Claude breaks it into tasks — you review and approve in the terminal
3. Claude writes the code and tests (≥95% coverage enforced automatically)
4. Opens a GitHub PR with all generated files
5. Waits for the PR to be merged, then triggers CI/CD
6. Marks the story **Done** in your Google Sheets tracker

---

## Prerequisites

- Python 3.12+
- A GitHub Personal Access Token
- An Anthropic API key
- A Google Cloud service account with Sheets API access

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure `chakra.yaml`

Open `chakra.yaml` and fill in:

```yaml
github:
  repo: "your-org/your-repo"       # target repo for PRs
  base_branch: "main"
  ci_workflow: "ci.yml"            # workflow file to trigger on merge

anthropic:
  model: "claude-opus-4-7"

google:
  credentials_path: "./credentials.json"
  spreadsheet_id: "your-sheet-id"  # see below for how to find this

tracker:
  sheet_name: "Chakra Tracker"

story:
  id_prefix: "CHAKRA"
```

### 3. GitHub Token

Create a Personal Access Token at **GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens**.

Required scopes: `repo`, `workflow`

```bash
export GITHUB_TOKEN=your_token_here
```

### 4. Anthropic API Key

```bash
export ANTHROPIC_API_KEY=your_key_here
```

### 5. Google Sheets — Service Account Setup

#### a. Create a Google Cloud project
- Go to [console.cloud.google.com](https://console.cloud.google.com)
- Click **New Project** → name it (e.g. `chakra`) → Create

#### b. Enable the Sheets API
- Go to **APIs & Services → Library**
- Search **Google Sheets API** → Enable

#### c. Create a Service Account
- Go to **APIs & Services → Credentials**
- Click **+ Create Credentials → Service Account**
- Name it `chakra-bot` → Create (skip optional steps)

#### d. Download the JSON key
- Click the service account → **Keys** tab → **Add Key → Create new key → JSON**
- Rename the downloaded file to `credentials.json`
- Place it in the project root (it is already git-ignored — safe to commit other files)

#### e. Find your Spreadsheet ID
Open your Google Sheet in a browser. The ID is the long string in the URL:

```
https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID_HERE/edit
```

Paste it into `chakra.yaml` under `google.spreadsheet_id`.

#### f. Share the sheet with the service account
- Open your Google Sheet → **Share**
- Paste the service account email (e.g. `chakra-bot@your-project.iam.gserviceaccount.com`)
- Grant **Editor** access

---

## Running

```bash
export GITHUB_TOKEN=...
export ANTHROPIC_API_KEY=...
python3 orchestrator.py story.txt
```

**Example `story.txt`:**
```
Add user login with email and password

Users should be able to register with an email and password,
log in, and receive a JWT token on success.
```

---

## Tracker (Google Sheets)

The sheet is auto-created on first run with these columns:

| Story ID | Story Title | Task | Status | Updated At |
|----------|-------------|------|--------|------------|

Status lifecycle: `Pending → Planning → Coding → Testing → PR Created → Done`

---

## Logs

All SDLC events are logged to `logs/chakra.log` (rotating, max 10MB × 5 backups).

- **DEBUG** level in the file — includes full Claude prompts and responses
- **INFO** level on stdout — step-by-step progress

```bash
tail -f logs/chakra.log
```

---

## Checkpoint & Resume

Chakra saves a checkpoint file (`story.chakra.json`) next to your story file after each phase completes. If a run fails or is interrupted, the next run resumes from the last successful phase — no re-planning, no re-approval prompt.

| Checkpoint `phase_reached` | What is skipped on next run |
|---|---|
| `planning` | Planning + human approval |
| `coding` | Planning + coding |
| `testing` | Planning + coding + testing |

The checkpoint file is deleted automatically when the run completes successfully.

**To force a fresh run** (re-plan from scratch):
```bash
rm story.chakra.json
python3 orchestrator.py story.txt
```

If you edit `story.txt` between runs, Chakra detects the content change (via SHA-256 hash), discards the old checkpoint, and starts fresh automatically.

---

## Security

| File | Status |
|------|--------|
| `credentials.json` | git-ignored — never committed |
| `.env` | git-ignored |
| `logs/` | git-ignored |
| `GITHUB_TOKEN` | env var only |
| `ANTHROPIC_API_KEY` | env var only |

---

## Project Structure

```
chakra/
├── orchestrator.py          # entry point
├── chakra.yaml              # configuration
├── CLAUDE.md                # Claude Code context
├── requirements.txt
├── agents/
│   └── sdlc_agent.py        # Claude API: plan / code / test
└── tools/
    ├── config.py            # config loader
    ├── logger.py            # logging setup
    ├── approval_tool.py     # terminal approval prompt
    ├── checkpoint_tool.py   # phase checkpoint save/load/clear
    ├── github_tool.py       # GitHub branch / PR / CI
    └── sheets_tool.py       # Google Sheets tracker
```
