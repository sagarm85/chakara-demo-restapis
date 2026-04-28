# Chakra

Agentic SDLC loop: user story → GitHub PR via Claude.

## Entry point
```bash
export GITHUB_TOKEN=...
export ANTHROPIC_API_KEY=...
python orchestrator.py story.txt
```

## Setup
1. `pip install -r requirements.txt`
2. Copy `chakra.yaml` and fill in `github.repo` and `google.spreadsheet_id`
3. **GitHub token** — create a Personal Access Token with scopes: `repo`, `workflow`. Export as `GITHUB_TOKEN`
4. **Google credentials** — create a Google Cloud project, enable the Sheets API, create a Service Account, download the JSON key as `credentials.json`, then share your target Google Sheet with the service account email
5. Export `ANTHROPIC_API_KEY`

> Note: `credentials.json` and `.env` are git-ignored. Never commit them.

## Stack
- Python 3.12
- `anthropic` SDK — LLM calls (plan/code/test)
- `PyGithub` — branch, commit, PR, CI dispatch
- `gspread` + `google-auth` — Google Sheets tracker
- `PyYAML` — config

## Flow
story.txt → plan (human approves) → code → test (≥95% coverage) → PR → poll merge → CI/CD → Done

> Note: `story.txt` is a plain-text file with the user story. The first line is used as the title.

## Logs
`logs/chakra.log` — rotating, DEBUG level with full Claude prompts/responses
