# Chakra

Agentic SDLC loop: user story → GitHub PR via Claude.

## Entry point
```bash
export GITHUB_TOKEN=...
export ANTHROPIC_API_KEY=...
python orchestrator.py story.txt
```

## Setup
1. Copy `chakra.yaml`, fill in `github.repo`, `google.spreadsheet_id`
2. Place Google service account key at `credentials.json`
3. `pip install -r requirements.txt`

## Stack
- Python 3.12
- `anthropic` SDK — LLM calls (plan/code/test)
- `PyGithub` — branch, commit, PR, CI dispatch
- `gspread` + `google-auth` — Google Sheets tracker
- `PyYAML` — config

## Flow
story.txt → plan (human approves) → code → test (≥95% coverage) → PR → poll merge → CI/CD → Done

## Logs
`logs/chakra.log` — rotating, DEBUG level with full Claude prompts/responses
