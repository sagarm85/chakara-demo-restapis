# Chakra Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CLI tool that reads a user story, autonomously plans/codes/tests it via Claude, gets one human approval, opens a GitHub PR, and marks it done in Google Sheets when merged.

**Architecture:** Linear blocking loop in `orchestrator.py` — each SDLC phase calls the appropriate tool or agent, updates Google Sheets, and moves to the next phase. One approval gate after planning; coding and testing run autonomously. Coverage is enforced at 95% via a retry loop before committing to GitHub.

**Tech Stack:** Python 3.12, `anthropic` SDK, `PyGithub`, `gspread` + `google-auth`, `PyYAML`, `pytest`, `pytest-cov`

---

## File Map

| File | Responsibility |
|------|---------------|
| `orchestrator.py` | Entry point; owns the SDLC loop and state transitions |
| `tools/config.py` | Load and parse `chakra.yaml` into typed dataclasses |
| `tools/logger.py` | Configure rotating file + stdout logging |
| `tools/approval_tool.py` | Terminal approval prompt; raises `ApprovalRejected` on rejection |
| `tools/sheets_tool.py` | Google Sheets read/write for the tracker |
| `tools/github_tool.py` | GitHub branch, commit, PR, poll, CI/CD dispatch |
| `agents/sdlc_agent.py` | Claude API calls for plan/code/test + local coverage measurement |
| `tests/tools/test_config.py` | Config loader tests |
| `tests/tools/test_logger.py` | Logger setup tests |
| `tests/tools/test_approval_tool.py` | Approval prompt tests |
| `tests/tools/test_sheets_tool.py` | Sheets tool tests (mock gspread) |
| `tests/tools/test_github_tool.py` | GitHub tool tests (mock PyGithub) |
| `tests/agents/test_sdlc_agent.py` | Agent tests (mock anthropic) |
| `tests/test_orchestrator.py` | Orchestrator integration tests (mock all tools) |

---

## Task 1: Project Bootstrap

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `chakra.yaml`
- Create: `CLAUDE.md`
- Create: `agents/__init__.py`
- Create: `tools/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/tools/__init__.py`
- Create: `tests/agents/__init__.py`

- [ ] **Step 1: Create directory structure**

```bash
cd /Users/sagarmahamuni/JOB_2026/AI/sdlc-project/chakra
mkdir -p agents tools tests/tools tests/agents logs
touch agents/__init__.py tools/__init__.py tests/__init__.py tests/tools/__init__.py tests/agents/__init__.py
```

- [ ] **Step 2: Write `requirements.txt`**

```
anthropic>=0.40.0
PyGithub>=2.3.0
gspread>=6.0.0
google-auth>=2.28.0
PyYAML>=6.0.1
pytest>=8.0.0
pytest-cov>=5.0.0
pytest-mock>=3.14.0
```

- [ ] **Step 3: Write `.gitignore`**

```
__pycache__/
*.pyc
*.pyo
.env
credentials.json
logs/
.coverage
htmlcov/
.pytest_cache/
*.egg-info/
dist/
build/
```

- [ ] **Step 4: Write `chakra.yaml` (template)**

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

- [ ] **Step 5: Write `CLAUDE.md`**

```markdown
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
```

- [ ] **Step 6: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 7: Commit**

```bash
git init
git add requirements.txt .gitignore chakra.yaml CLAUDE.md agents/__init__.py tools/__init__.py tests/__init__.py tests/tools/__init__.py tests/agents/__init__.py
git commit -m "chore: bootstrap chakra phase 1 project"
```

---

## Task 2: Config Loader

**Files:**
- Create: `tools/config.py`
- Create: `tests/tools/test_config.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/tools/test_config.py`:

```python
import pytest
import yaml
from pathlib import Path
from tools.config import load_config, Config, GitHubConfig, AnthropicConfig, GoogleConfig, TrackerConfig, StoryConfig


VALID_YAML = """
github:
  repo: "owner/repo"
  base_branch: "main"
  ci_workflow: "ci.yml"
anthropic:
  model: "claude-opus-4-7"
google:
  credentials_path: "./credentials.json"
  spreadsheet_id: "abc123"
tracker:
  sheet_name: "Chakra Tracker"
story:
  id_prefix: "CHAKRA"
"""


def test_load_config_returns_typed_config(tmp_path):
    cfg_file = tmp_path / "chakra.yaml"
    cfg_file.write_text(VALID_YAML)
    config = load_config(str(cfg_file))
    assert isinstance(config, Config)
    assert isinstance(config.github, GitHubConfig)
    assert isinstance(config.anthropic, AnthropicConfig)
    assert isinstance(config.google, GoogleConfig)
    assert isinstance(config.tracker, TrackerConfig)
    assert isinstance(config.story, StoryConfig)


def test_load_config_values(tmp_path):
    cfg_file = tmp_path / "chakra.yaml"
    cfg_file.write_text(VALID_YAML)
    config = load_config(str(cfg_file))
    assert config.github.repo == "owner/repo"
    assert config.github.base_branch == "main"
    assert config.github.ci_workflow == "ci.yml"
    assert config.anthropic.model == "claude-opus-4-7"
    assert config.google.credentials_path == "./credentials.json"
    assert config.google.spreadsheet_id == "abc123"
    assert config.tracker.sheet_name == "Chakra Tracker"
    assert config.story.id_prefix == "CHAKRA"


def test_load_config_missing_field_raises(tmp_path):
    bad_yaml = """
github:
  repo: "owner/repo"
anthropic:
  model: "claude-opus-4-7"
"""
    cfg_file = tmp_path / "chakra.yaml"
    cfg_file.write_text(bad_yaml)
    with pytest.raises((KeyError, TypeError)):
        load_config(str(cfg_file))


def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/chakra.yaml")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/tools/test_config.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tools.config'`

- [ ] **Step 3: Write `tools/config.py`**

```python
from dataclasses import dataclass
import yaml


@dataclass
class GitHubConfig:
    repo: str
    base_branch: str
    ci_workflow: str


@dataclass
class AnthropicConfig:
    model: str


@dataclass
class GoogleConfig:
    credentials_path: str
    spreadsheet_id: str


@dataclass
class TrackerConfig:
    sheet_name: str


@dataclass
class StoryConfig:
    id_prefix: str


@dataclass
class Config:
    github: GitHubConfig
    anthropic: AnthropicConfig
    google: GoogleConfig
    tracker: TrackerConfig
    story: StoryConfig


def load_config(path: str = "chakra.yaml") -> Config:
    with open(path) as f:
        data = yaml.safe_load(f)
    return Config(
        github=GitHubConfig(**data["github"]),
        anthropic=AnthropicConfig(**data["anthropic"]),
        google=GoogleConfig(**data["google"]),
        tracker=TrackerConfig(**data["tracker"]),
        story=StoryConfig(**data["story"]),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/tools/test_config.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add tools/config.py tests/tools/test_config.py
git commit -m "feat: add config loader with typed dataclasses"
```

---

## Task 3: Logging Setup

**Files:**
- Create: `tools/logger.py`
- Create: `tests/tools/test_logger.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/tools/test_logger.py`:

```python
import logging
import logging.handlers
from pathlib import Path
from tools.logger import setup_logging


def test_setup_logging_creates_logs_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    setup_logging()
    assert (tmp_path / "logs").is_dir()


def test_setup_logging_creates_log_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    setup_logging()
    logger = logging.getLogger("test.chakra")
    logger.info("test message")
    log_file = tmp_path / "logs" / "chakra.log"
    assert log_file.exists()
    assert "test message" in log_file.read_text()


def test_setup_logging_root_level_is_debug(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    setup_logging()
    assert logging.getLogger().level == logging.DEBUG


def test_setup_logging_has_two_handlers(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Reset root handlers to avoid cross-test pollution
    root = logging.getLogger()
    root.handlers.clear()
    setup_logging()
    assert len(root.handlers) == 2


def test_debug_messages_go_to_file_not_stdout(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    root = logging.getLogger()
    root.handlers.clear()
    setup_logging()
    logging.getLogger("test").debug("secret debug")
    captured = capsys.readouterr()
    assert "secret debug" not in captured.out
    log_content = (tmp_path / "logs" / "chakra.log").read_text()
    assert "secret debug" in log_content
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/tools/test_logger.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tools.logger'`

- [ ] **Step 3: Write `tools/logger.py`**

```python
import logging
import logging.handlers
from pathlib import Path


def setup_logging() -> None:
    Path("logs").mkdir(exist_ok=True)
    fmt = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
    formatter = logging.Formatter(fmt)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    file_handler = logging.handlers.RotatingFileHandler(
        "logs/chakra.log", maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    root.addHandler(file_handler)
    root.addHandler(console_handler)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/tools/test_logger.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add tools/logger.py tests/tools/test_logger.py
git commit -m "feat: add rotating file + stdout logging setup"
```

---

## Task 4: Approval Tool

**Files:**
- Create: `tools/approval_tool.py`
- Create: `tests/tools/test_approval_tool.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/tools/test_approval_tool.py`:

```python
import pytest
from unittest.mock import patch
from tools.approval_tool import prompt_approval, ApprovalRejected


def test_prompt_approval_y_returns_true():
    with patch("builtins.input", return_value="y"):
        result = prompt_approval("Test Label", "Test content")
    assert result is True


def test_prompt_approval_n_raises_approval_rejected():
    with patch("builtins.input", side_effect=["n", ""]):
        with pytest.raises(ApprovalRejected):
            prompt_approval("Test Label", "Test content")


def test_prompt_approval_n_with_reason_stores_reason():
    with patch("builtins.input", side_effect=["n", "needs more detail"]):
        with pytest.raises(ApprovalRejected) as exc_info:
            prompt_approval("Test Label", "Test content")
    assert exc_info.value.reason == "needs more detail"


def test_prompt_approval_invalid_then_y_accepts():
    with patch("builtins.input", side_effect=["maybe", "y"]):
        result = prompt_approval("Test Label", "Test content")
    assert result is True


def test_prompt_approval_prints_label(capsys):
    with patch("builtins.input", return_value="y"):
        prompt_approval("My Label", "some content")
    captured = capsys.readouterr()
    assert "My Label" in captured.out


def test_prompt_approval_prints_content(capsys):
    with patch("builtins.input", return_value="y"):
        prompt_approval("Label", "important content here")
    captured = capsys.readouterr()
    assert "important content here" in captured.out


def test_approval_rejected_has_message():
    exc = ApprovalRejected("bad plan")
    assert "bad plan" in str(exc)
    assert exc.reason == "bad plan"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/tools/test_approval_tool.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tools.approval_tool'`

- [ ] **Step 3: Write `tools/approval_tool.py`**

```python
import logging

logger = logging.getLogger(__name__)


class ApprovalRejected(Exception):
    def __init__(self, reason: str = ""):
        self.reason = reason
        super().__init__(f"Approval rejected: {reason}")


def prompt_approval(label: str, content: str) -> bool:
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")
    print(content)
    print(f"{'=' * 60}\n")

    while True:
        response = input("Approve? [y/n]: ").strip().lower()
        if response == "y":
            logger.info("Approval granted for: %s", label)
            return True
        elif response == "n":
            reason = input("Rejection reason (optional): ").strip()
            logger.info("Approval rejected for: %s — reason: %s", label, reason)
            raise ApprovalRejected(reason)
        else:
            print("Please enter 'y' or 'n'")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/tools/test_approval_tool.py -v
```

Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add tools/approval_tool.py tests/tools/test_approval_tool.py
git commit -m "feat: add terminal approval tool with ApprovalRejected exception"
```

---

## Task 5: Sheets Tool

**Files:**
- Create: `tools/sheets_tool.py`
- Create: `tests/tools/test_sheets_tool.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/tools/test_sheets_tool.py`:

```python
import pytest
from unittest.mock import MagicMock, patch, call
from tools.sheets_tool import SheetsTool


@pytest.fixture
def mock_worksheet():
    ws = MagicMock()
    ws.get_all_records.return_value = []
    return ws


@pytest.fixture
def sheets_tool(mock_worksheet):
    with patch("tools.sheets_tool.gspread") as mock_gspread, \
         patch("tools.sheets_tool.Credentials") as mock_creds:
        mock_client = MagicMock()
        mock_gspread.authorize.return_value = mock_client
        mock_spreadsheet = MagicMock()
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        tool = SheetsTool("./credentials.json", "sheet-id-abc", "Chakra Tracker")
        tool._sheet = mock_worksheet
        yield tool


def test_upsert_row_appends_new_row(sheets_tool, mock_worksheet):
    mock_worksheet.get_all_records.return_value = []
    sheets_tool.upsert_row("CHAKRA-001", "Add login", "setup", "Pending")
    mock_worksheet.append_row.assert_called_once()
    row = mock_worksheet.append_row.call_args[0][0]
    assert row[0] == "CHAKRA-001"
    assert row[1] == "Add login"
    assert row[2] == "setup"
    assert row[3] == "Pending"


def test_upsert_row_updates_existing_row(sheets_tool, mock_worksheet):
    mock_worksheet.get_all_records.return_value = [
        {"Story ID": "CHAKRA-001", "Story Title": "Add login", "Task": "setup",
         "Status": "Pending", "Updated At": "old"}
    ]
    sheets_tool.upsert_row("CHAKRA-001", "Add login", "setup", "Coding")
    mock_worksheet.update.assert_called_once()
    update_args = mock_worksheet.update.call_args[0]
    assert update_args[0] == "A2:E2"
    assert update_args[1][0][3] == "Coding"


def test_update_status_updates_correct_cells(sheets_tool, mock_worksheet):
    mock_worksheet.get_all_records.return_value = [
        {"Story ID": "CHAKRA-001", "Story Title": "Add login", "Task": "overall",
         "Status": "Planning", "Updated At": "old"}
    ]
    sheets_tool.update_status("CHAKRA-001", "overall", "Coding")
    mock_worksheet.update_cell.assert_any_call(2, 4, "Coding")


def test_update_status_updates_timestamp(sheets_tool, mock_worksheet):
    mock_worksheet.get_all_records.return_value = [
        {"Story ID": "CHAKRA-001", "Story Title": "Add login", "Task": "overall",
         "Status": "Planning", "Updated At": "old"}
    ]
    sheets_tool.update_status("CHAKRA-001", "overall", "Coding")
    calls = mock_worksheet.update_cell.call_args_list
    col_5_calls = [c for c in calls if c[0][1] == 5]
    assert len(col_5_calls) == 1
    timestamp_value = col_5_calls[0][0][2]
    assert "UTC" in timestamp_value


def test_update_status_row_not_found_logs_warning(sheets_tool, mock_worksheet, caplog):
    import logging
    mock_worksheet.get_all_records.return_value = []
    with caplog.at_level(logging.WARNING):
        sheets_tool.update_status("CHAKRA-999", "overall", "Done")
    assert "not found" in caplog.text.lower()


def test_get_all_story_ids_returns_ids(sheets_tool, mock_worksheet):
    mock_worksheet.get_all_records.return_value = [
        {"Story ID": "CHAKRA-001", "Story Title": "A", "Task": "t1", "Status": "Done", "Updated At": "x"},
        {"Story ID": "CHAKRA-002", "Story Title": "B", "Task": "t1", "Status": "Done", "Updated At": "x"},
    ]
    ids = sheets_tool.get_all_story_ids()
    assert ids == ["CHAKRA-001", "CHAKRA-002"]


def test_get_all_story_ids_empty_sheet(sheets_tool, mock_worksheet):
    mock_worksheet.get_all_records.return_value = []
    assert sheets_tool.get_all_story_ids() == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/tools/test_sheets_tool.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tools.sheets_tool'`

- [ ] **Step 3: Write `tools/sheets_tool.py`**

```python
import logging
from datetime import datetime, timezone

import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
COLUMNS = ["Story ID", "Story Title", "Task", "Status", "Updated At"]


class SheetsTool:
    def __init__(self, credentials_path: str, spreadsheet_id: str, sheet_name: str):
        creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
        client = gspread.authorize(creds)
        self._spreadsheet = client.open_by_key(spreadsheet_id)
        self._sheet = self._get_or_create_sheet(sheet_name)

    def _get_or_create_sheet(self, name: str) -> gspread.Worksheet:
        try:
            ws = self._spreadsheet.worksheet(name)
        except gspread.WorksheetNotFound:
            ws = self._spreadsheet.add_worksheet(name, rows=1000, cols=len(COLUMNS))
            ws.append_row(COLUMNS)
            logger.info("Created new sheet: %s", name)
        return ws

    def _now(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    def _find_row(self, story_id: str, task: str) -> int | None:
        records = self._sheet.get_all_records()
        for i, row in enumerate(records, start=2):
            if row.get("Story ID") == story_id and row.get("Task") == task:
                return i
        return None

    def upsert_row(self, story_id: str, story_title: str, task: str, status: str) -> None:
        row_num = self._find_row(story_id, task)
        now = self._now()
        if row_num:
            self._sheet.update(f"A{row_num}:E{row_num}", [[story_id, story_title, task, status, now]])
            logger.info("Sheets update: %s / %s → %s", story_id, task, status)
        else:
            self._sheet.append_row([story_id, story_title, task, status, now])
            logger.info("Sheets insert: %s / %s → %s", story_id, task, status)

    def update_status(self, story_id: str, task: str, status: str) -> None:
        row_num = self._find_row(story_id, task)
        if not row_num:
            logger.warning("Row not found for %s / %s", story_id, task)
            return
        now = self._now()
        self._sheet.update_cell(row_num, 4, status)
        self._sheet.update_cell(row_num, 5, now)
        logger.info("Sheets status: %s / %s → %s", story_id, task, status)

    def get_all_story_ids(self) -> list[str]:
        records = self._sheet.get_all_records()
        return [r["Story ID"] for r in records if r.get("Story ID")]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/tools/test_sheets_tool.py -v
```

Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add tools/sheets_tool.py tests/tools/test_sheets_tool.py
git commit -m "feat: add Google Sheets tracker tool"
```

---

## Task 6: GitHub Tool

**Files:**
- Create: `tools/github_tool.py`
- Create: `tests/tools/test_github_tool.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/tools/test_github_tool.py`:

```python
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from tools.github_tool import GitHubTool


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    return repo


@pytest.fixture
def github_tool(mock_repo):
    with patch("tools.github_tool.Github") as mock_gh_class:
        mock_gh = MagicMock()
        mock_gh_class.return_value = mock_gh
        mock_gh.get_repo.return_value = mock_repo
        tool = GitHubTool("fake-token", "owner/repo")
        tool._repo = mock_repo
        yield tool


def test_create_branch_calls_create_git_ref(github_tool, mock_repo):
    mock_branch = MagicMock()
    mock_branch.commit.sha = "abc123"
    mock_repo.get_branch.return_value = mock_branch
    github_tool.create_branch("chakra/CHAKRA-001-feature", "main")
    mock_repo.create_git_ref.assert_called_once_with(
        "refs/heads/chakra/CHAKRA-001-feature", "abc123"
    )


def test_commit_files_creates_blob_tree_and_commit(github_tool, mock_repo):
    mock_ref = MagicMock()
    mock_ref.object.sha = "ref-sha"
    mock_repo.get_git_ref.return_value = mock_ref

    mock_base_commit = MagicMock()
    mock_base_commit.tree = MagicMock()
    mock_repo.get_git_commit.return_value = mock_base_commit

    mock_blob = MagicMock()
    mock_blob.sha = "blob-sha"
    mock_repo.create_git_blob.return_value = mock_blob

    mock_tree = MagicMock()
    mock_repo.create_git_tree.return_value = mock_tree

    mock_new_commit = MagicMock()
    mock_new_commit.sha = "new-commit-sha"
    mock_repo.create_git_commit.return_value = mock_new_commit

    sha = github_tool.commit_files("chakra/CHAKRA-001", {"src/app.py": "print('hi')"}, "feat: add feature")
    mock_repo.create_git_blob.assert_called_once_with("print('hi')", "utf-8")
    mock_repo.create_git_tree.assert_called_once()
    mock_repo.create_git_commit.assert_called_once()
    mock_ref.edit.assert_called_once_with("new-commit-sha")
    assert sha == "new-commit-sha"


def test_open_pr_returns_url_and_number(github_tool, mock_repo):
    mock_pr = MagicMock()
    mock_pr.html_url = "https://github.com/owner/repo/pull/42"
    mock_pr.number = 42
    mock_repo.create_pull.return_value = mock_pr
    url, number = github_tool.open_pr("chakra/branch", "main", "title", "body")
    assert url == "https://github.com/owner/repo/pull/42"
    assert number == 42


def test_poll_merge_returns_when_merged(github_tool, mock_repo):
    mock_pr = MagicMock()
    mock_pr.merged = True
    mock_pr.state = "closed"
    mock_repo.get_pull.return_value = mock_pr
    github_tool.poll_merge(42, interval_seconds=0)
    mock_repo.get_pull.assert_called_once_with(42)


def test_poll_merge_retries_until_merged(github_tool, mock_repo):
    open_pr = MagicMock()
    open_pr.merged = False
    open_pr.state = "open"
    merged_pr = MagicMock()
    merged_pr.merged = True
    mock_repo.get_pull.side_effect = [open_pr, merged_pr]
    with patch("tools.github_tool.time.sleep"):
        github_tool.poll_merge(42, interval_seconds=1)
    assert mock_repo.get_pull.call_count == 2


def test_poll_merge_raises_on_closed_without_merge(github_tool, mock_repo):
    mock_pr = MagicMock()
    mock_pr.merged = False
    mock_pr.state = "closed"
    mock_repo.get_pull.return_value = mock_pr
    with pytest.raises(RuntimeError, match="closed without merging"):
        github_tool.poll_merge(42, interval_seconds=0)


def test_trigger_cicd_dispatches_workflow(github_tool, mock_repo):
    mock_workflow = MagicMock()
    mock_repo.get_workflow.return_value = mock_workflow
    github_tool.trigger_cicd("ci.yml", "main")
    mock_repo.get_workflow.assert_called_once_with("ci.yml")
    mock_workflow.create_dispatch.assert_called_once_with("main")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/tools/test_github_tool.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tools.github_tool'`

- [ ] **Step 3: Write `tools/github_tool.py`**

```python
import logging
import time

from github import Github, InputGitTreeElement

logger = logging.getLogger(__name__)


class GitHubTool:
    def __init__(self, token: str, repo_name: str):
        self._gh = Github(token)
        self._repo = self._gh.get_repo(repo_name)

    def create_branch(self, branch_name: str, base_branch: str = "main") -> None:
        base = self._repo.get_branch(base_branch)
        self._repo.create_git_ref(f"refs/heads/{branch_name}", base.commit.sha)
        logger.info("Created branch: %s from %s", branch_name, base_branch)

    def commit_files(self, branch: str, files: dict[str, str], message: str) -> str:
        ref = self._repo.get_git_ref(f"heads/{branch}")
        base_commit = self._repo.get_git_commit(ref.object.sha)

        tree_elements = []
        for path, content in files.items():
            blob = self._repo.create_git_blob(content, "utf-8")
            tree_elements.append(
                InputGitTreeElement(path=path, mode="100644", type="blob", sha=blob.sha)
            )

        new_tree = self._repo.create_git_tree(tree_elements, base_commit.tree)
        new_commit = self._repo.create_git_commit(message, new_tree, [base_commit])
        ref.edit(new_commit.sha)
        logger.info("Committed %d files to %s: %s", len(files), branch, new_commit.sha)
        return new_commit.sha

    def open_pr(self, branch: str, base_branch: str, title: str, body: str) -> tuple[str, int]:
        pr = self._repo.create_pull(title=title, body=body, head=branch, base=base_branch)
        logger.info("Opened PR #%d: %s", pr.number, pr.html_url)
        return pr.html_url, pr.number

    def poll_merge(self, pr_number: int, interval_seconds: int = 30) -> None:
        logger.info("Polling PR #%d for merge every %ds...", pr_number, interval_seconds)
        while True:
            pr = self._repo.get_pull(pr_number)
            if pr.merged:
                logger.info("PR #%d merged", pr_number)
                return
            if pr.state == "closed":
                raise RuntimeError(f"PR #{pr_number} was closed without merging")
            logger.debug("PR #%d still open, checking again in %ds", pr_number, interval_seconds)
            time.sleep(interval_seconds)

    def trigger_cicd(self, workflow: str, ref: str) -> None:
        workflow_obj = self._repo.get_workflow(workflow)
        workflow_obj.create_dispatch(ref)
        logger.info("Triggered workflow %s on ref %s", workflow, ref)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/tools/test_github_tool.py -v
```

Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add tools/github_tool.py tests/tools/test_github_tool.py
git commit -m "feat: add GitHub tool (branch, commit, PR, poll, CI dispatch)"
```

---

## Task 7: SDLC Agent

**Files:**
- Create: `agents/sdlc_agent.py`
- Create: `tests/agents/test_sdlc_agent.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/agents/test_sdlc_agent.py`:

```python
import json
import pytest
from unittest.mock import MagicMock, patch
from agents.sdlc_agent import SDLCAgent


PLAN_RESPONSE = '```json\n[{"task": "setup", "description": "Create project structure"}]\n```'
CODE_RESPONSE = '```json\n{"src/app.py": "def hello():\\n    return \'hello\'"}\n```'
TEST_RESPONSE = '```json\n{"tests/test_app.py": "from src.app import hello\\ndef test_hello():\\n    assert hello() == \'hello\'"}\n```'


@pytest.fixture
def agent():
    with patch("agents.sdlc_agent.anthropic.Anthropic"):
        a = SDLCAgent("fake-key", "claude-opus-4-7")
        a._client = MagicMock()
        return a


def _mock_response(text: str):
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    return msg


def test_plan_returns_list_of_dicts(agent):
    agent._client.messages.create.return_value = _mock_response(PLAN_RESPONSE)
    result = agent.plan("As a user I want a hello endpoint")
    assert isinstance(result, list)
    assert result[0]["task"] == "setup"
    assert result[0]["description"] == "Create project structure"


def test_plan_includes_rejection_feedback_in_prompt(agent):
    agent._client.messages.create.return_value = _mock_response(PLAN_RESPONSE)
    agent.plan("story", rejection_feedback="too vague")
    call_kwargs = agent._client.messages.create.call_args
    user_content = call_kwargs[1]["messages"][0]["content"]
    assert "too vague" in user_content


def test_plan_no_feedback_omits_feedback_section(agent):
    agent._client.messages.create.return_value = _mock_response(PLAN_RESPONSE)
    agent.plan("story", rejection_feedback="")
    call_kwargs = agent._client.messages.create.call_args
    user_content = call_kwargs[1]["messages"][0]["content"]
    assert "rejection" not in user_content.lower()


def test_code_returns_dict_of_files(agent):
    agent._client.messages.create.return_value = _mock_response(CODE_RESPONSE)
    tasks = [{"task": "setup", "description": "Create project structure"}]
    result = agent.code("story", tasks)
    assert "src/app.py" in result
    assert "def hello" in result["src/app.py"]


def test_test_returns_dict_of_test_files(agent):
    agent._client.messages.create.return_value = _mock_response(TEST_RESPONSE)
    code = {"src/app.py": "def hello():\n    return 'hello'"}
    result = agent.test("story", code)
    assert "tests/test_app.py" in result


def test_test_includes_coverage_feedback_in_prompt(agent):
    agent._client.messages.create.return_value = _mock_response(TEST_RESPONSE)
    agent.test("story", {}, coverage_feedback="TOTAL 10 5 50%")
    call_kwargs = agent._client.messages.create.call_args
    user_content = call_kwargs[1]["messages"][0]["content"]
    assert "TOTAL 10 5 50%" in user_content


def test_measure_coverage_returns_float_and_report(agent, tmp_path):
    code_files = {"src/app.py": "def hello():\n    return 'hello'\n"}
    test_files = {
        "tests/__init__.py": "",
        "tests/test_app.py": (
            "import sys, os\n"
            "sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))\n"
            "from src.app import hello\n"
            "def test_hello():\n"
            "    assert hello() == 'hello'\n"
        ),
    }
    coverage, report = agent.measure_coverage(code_files, test_files)
    assert isinstance(coverage, float)
    assert isinstance(report, str)


def test_measure_coverage_returns_zero_on_no_tests(agent):
    coverage, report = agent.measure_coverage({"src/app.py": "x = 1"}, {})
    assert coverage == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/agents/test_sdlc_agent.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'agents.sdlc_agent'`

- [ ] **Step 3: Write `agents/sdlc_agent.py`**

```python
import json
import logging
import re
import subprocess
import tempfile
from pathlib import Path

import anthropic

logger = logging.getLogger(__name__)


class SDLCAgent:
    def __init__(self, api_key: str, model: str):
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def _call(self, system: str, user: str) -> str:
        logger.debug("Claude prompt (%s): %s", self._model, user[:500])
        response = self._client.messages.create(
            model=self._model,
            max_tokens=8096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        result = response.content[0].text
        logger.debug("Claude response: %s", result[:500])
        return result

    def _extract_json(self, text: str):
        match = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        return json.loads(text)

    def plan(self, story: str, rejection_feedback: str = "") -> list[dict]:
        feedback_section = (
            f"\n\nPrevious rejection feedback: {rejection_feedback}"
            if rejection_feedback
            else ""
        )
        user = (
            f"Analyze this user story and break it into implementation tasks."
            f"{feedback_section}\n\nUser story:\n{story}\n\n"
            f"Return a JSON array of tasks, each with \"task\" (short name) and "
            f"\"description\" (what to implement).\n"
            f'Format: ```json\n[{{"task": "...", "description": "..."}}]\n```'
        )
        system = (
            "You are a senior software engineer breaking user stories into "
            "implementation tasks. Be specific and actionable."
        )
        response = self._call(system, user)
        tasks = self._extract_json(response)
        logger.info("Planned %d tasks", len(tasks))
        return tasks

    def code(self, story: str, tasks: list[dict]) -> dict[str, str]:
        tasks_text = "\n".join(
            f"- {t['task']}: {t['description']}" for t in tasks
        )
        user = (
            f"Generate Python implementation code for this user story.\n\n"
            f"User story: {story}\n\nTasks to implement:\n{tasks_text}\n\n"
            f"Return a JSON object mapping filename to file content.\n"
            f'Format: ```json\n{{"path/to/file.py": "# file content"}}\n```'
        )
        system = (
            "You are a senior Python developer. "
            "Write clean, well-structured Python 3.12 code."
        )
        response = self._call(system, user)
        files = self._extract_json(response)
        logger.info("Generated %d code files", len(files))
        return files

    def test(
        self,
        story: str,
        code: dict[str, str],
        coverage_feedback: str = "",
    ) -> dict[str, str]:
        code_summary = "\n\n".join(
            f"# {fname}\n{content}" for fname, content in code.items()
        )
        feedback_section = (
            f"\n\nCoverage feedback (improve to reach 95%):\n{coverage_feedback}"
            if coverage_feedback
            else ""
        )
        user = (
            f"Generate pytest tests achieving ≥95% line coverage for this code."
            f"{feedback_section}\n\nUser story: {story}\n\nCode to test:\n{code_summary}\n\n"
            f"Return a JSON object mapping test filename to test content.\n"
            f'Format: ```json\n{{"tests/test_file.py": "# test content"}}\n```'
        )
        system = (
            "You are a senior Python test engineer. "
            "Write thorough pytest tests targeting ≥95% line coverage."
        )
        response = self._call(system, user)
        files = self._extract_json(response)
        logger.info("Generated %d test files", len(files))
        return files

    def measure_coverage(
        self,
        code_files: dict[str, str],
        test_files: dict[str, str],
    ) -> tuple[float, str]:
        if not test_files:
            logger.warning("No test files provided — coverage is 0%%")
            return 0.0, "No test files"

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for fname, content in {**code_files, **test_files}.items():
                fpath = tmp_path / fname
                fpath.parent.mkdir(parents=True, exist_ok=True)
                fpath.write_text(content)

            result = subprocess.run(
                ["python", "-m", "pytest", "--cov=.", "--cov-report=term-missing", "-q"],
                cwd=tmp_path,
                capture_output=True,
                text=True,
            )
            output = result.stdout + result.stderr
            logger.debug("Coverage output:\n%s", output)

            match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
            coverage = float(match.group(1)) if match else 0.0
            logger.info("Coverage measured: %.0f%%", coverage)
            return coverage, output
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/agents/test_sdlc_agent.py -v
```

Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add agents/sdlc_agent.py tests/agents/test_sdlc_agent.py
git commit -m "feat: add SDLCAgent (plan/code/test via Claude, coverage measurement)"
```

---

## Task 8: Orchestrator

**Files:**
- Create: `orchestrator.py`
- Create: `tests/test_orchestrator.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_orchestrator.py`:

```python
import sys
import pytest
from unittest.mock import MagicMock, patch, call
import orchestrator


@pytest.fixture
def mock_config():
    from tools.config import Config, GitHubConfig, AnthropicConfig, GoogleConfig, TrackerConfig, StoryConfig
    return Config(
        github=GitHubConfig(repo="owner/repo", base_branch="main", ci_workflow="ci.yml"),
        anthropic=AnthropicConfig(model="claude-opus-4-7"),
        google=GoogleConfig(credentials_path="./credentials.json", spreadsheet_id="sid"),
        tracker=TrackerConfig(sheet_name="Chakra Tracker"),
        story=StoryConfig(id_prefix="CHAKRA"),
    )


@pytest.fixture
def mock_tools():
    github = MagicMock()
    github.open_pr.return_value = ("https://github.com/owner/repo/pull/1", 1)
    sheets = MagicMock()
    sheets.get_all_story_ids.return_value = []
    agent = MagicMock()
    agent.plan.return_value = [{"task": "setup", "description": "do setup"}]
    agent.code.return_value = {"src/app.py": "x = 1"}
    agent.test.return_value = {"tests/test_app.py": "def test_x(): pass"}
    agent.measure_coverage.return_value = (100.0, "TOTAL 1 0 100%")
    return github, sheets, agent


def _run_with_mocks(tmp_path, mock_config, github, sheets, agent, story_text="As a user I want X"):
    story_file = tmp_path / "story.txt"
    story_file.write_text(story_text)

    with patch("orchestrator.load_config", return_value=mock_config), \
         patch("orchestrator.setup_logging"), \
         patch("orchestrator.GitHubTool", return_value=github), \
         patch("orchestrator.SheetsTool", return_value=sheets), \
         patch("orchestrator.SDLCAgent", return_value=agent), \
         patch("orchestrator.prompt_approval", return_value=True), \
         patch.dict("os.environ", {"GITHUB_TOKEN": "tok", "ANTHROPIC_API_KEY": "key"}):
        orchestrator.run(str(story_file))


def test_happy_path_calls_all_steps(tmp_path, mock_config, mock_tools):
    github, sheets, agent = mock_tools
    _run_with_mocks(tmp_path, mock_config, github, sheets, agent)

    agent.plan.assert_called_once()
    agent.code.assert_called_once()
    agent.test.assert_called_once()
    github.create_branch.assert_called_once()
    github.commit_files.assert_called_once()
    github.open_pr.assert_called_once()
    github.poll_merge.assert_called_once()
    github.trigger_cicd.assert_called_once()


def test_sheets_status_sequence(tmp_path, mock_config, mock_tools):
    github, sheets, agent = mock_tools
    _run_with_mocks(tmp_path, mock_config, github, sheets, agent)

    status_calls = [c[0][2] for c in sheets.update_status.call_args_list]
    assert "Planning" in status_calls
    assert "Coding" in status_calls
    assert "Testing" in status_calls
    assert "PR Created" in status_calls
    assert "Done" in status_calls


def test_planning_rejection_retries_with_feedback(tmp_path, mock_config, mock_tools):
    from tools.approval_tool import ApprovalRejected
    github, sheets, agent = mock_tools

    story_file = tmp_path / "story.txt"
    story_file.write_text("story")

    approve_calls = [ApprovalRejected("too vague"), True]
    with patch("orchestrator.load_config", return_value=mock_config), \
         patch("orchestrator.setup_logging"), \
         patch("orchestrator.GitHubTool", return_value=github), \
         patch("orchestrator.SheetsTool", return_value=sheets), \
         patch("orchestrator.SDLCAgent", return_value=agent), \
         patch("orchestrator.prompt_approval", side_effect=approve_calls), \
         patch.dict("os.environ", {"GITHUB_TOKEN": "tok", "ANTHROPIC_API_KEY": "key"}):
        orchestrator.run(str(story_file))

    assert agent.plan.call_count == 2
    second_call_kwargs = agent.plan.call_args_list[1][1]
    assert second_call_kwargs["rejection_feedback"] == "too vague"


def test_planning_rejected_max_retries_exits(tmp_path, mock_config, mock_tools):
    from tools.approval_tool import ApprovalRejected
    github, sheets, agent = mock_tools

    story_file = tmp_path / "story.txt"
    story_file.write_text("story")

    with patch("orchestrator.load_config", return_value=mock_config), \
         patch("orchestrator.setup_logging"), \
         patch("orchestrator.GitHubTool", return_value=github), \
         patch("orchestrator.SheetsTool", return_value=sheets), \
         patch("orchestrator.SDLCAgent", return_value=agent), \
         patch("orchestrator.prompt_approval", side_effect=ApprovalRejected("bad")), \
         patch.dict("os.environ", {"GITHUB_TOKEN": "tok", "ANTHROPIC_API_KEY": "key"}):
        with pytest.raises(SystemExit) as exc_info:
            orchestrator.run(str(story_file))
    assert exc_info.value.code == 1


def test_low_coverage_retries_test_generation(tmp_path, mock_config, mock_tools):
    github, sheets, agent = mock_tools
    agent.measure_coverage.side_effect = [
        (50.0, "TOTAL 10 5 50%"),
        (96.0, "TOTAL 10 0 96%"),
    ]
    _run_with_mocks(tmp_path, mock_config, github, sheets, agent)
    assert agent.test.call_count == 2
    second_call_kwargs = agent.test.call_args_list[1][1]
    assert "50%" in second_call_kwargs["coverage_feedback"]


def test_coverage_below_95_after_max_retries_exits(tmp_path, mock_config, mock_tools):
    github, sheets, agent = mock_tools
    agent.measure_coverage.return_value = (40.0, "TOTAL 10 6 40%")

    story_file = tmp_path / "story.txt"
    story_file.write_text("story")

    with patch("orchestrator.load_config", return_value=mock_config), \
         patch("orchestrator.setup_logging"), \
         patch("orchestrator.GitHubTool", return_value=github), \
         patch("orchestrator.SheetsTool", return_value=sheets), \
         patch("orchestrator.SDLCAgent", return_value=agent), \
         patch("orchestrator.prompt_approval", return_value=True), \
         patch.dict("os.environ", {"GITHUB_TOKEN": "tok", "ANTHROPIC_API_KEY": "key"}):
        with pytest.raises(SystemExit) as exc_info:
            orchestrator.run(str(story_file))
    assert exc_info.value.code == 1


def test_branch_name_uses_story_id_and_title(tmp_path, mock_config, mock_tools):
    github, sheets, agent = mock_tools
    _run_with_mocks(tmp_path, mock_config, github, sheets, agent, "Add user login feature")
    branch_arg = github.create_branch.call_args[0][0]
    assert branch_arg.startswith("chakra/CHAKRA-")
    assert "add-user-login" in branch_arg


def test_missing_story_file_exits(tmp_path, mock_config, mock_tools):
    github, sheets, agent = mock_tools
    with patch("orchestrator.load_config", return_value=mock_config), \
         patch("orchestrator.setup_logging"), \
         patch.dict("os.environ", {"GITHUB_TOKEN": "tok", "ANTHROPIC_API_KEY": "key"}):
        with pytest.raises((FileNotFoundError, SystemExit)):
            orchestrator.run(str(tmp_path / "nonexistent.txt"))
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_orchestrator.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'orchestrator'`

- [ ] **Step 3: Write `orchestrator.py`**

```python
import logging
import os
import re
import sys
from pathlib import Path

from agents.sdlc_agent import SDLCAgent
from tools.approval_tool import ApprovalRejected, prompt_approval
from tools.config import load_config
from tools.github_tool import GitHubTool
from tools.logger import setup_logging
from tools.sheets_tool import SheetsTool

MAX_RETRIES = 3


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40]


def _next_story_id(prefix: str, sheets: SheetsTool) -> str:
    existing = sheets.get_all_story_ids()
    numbers = []
    for sid in existing:
        match = re.match(rf"{re.escape(prefix)}-(\d+)", sid)
        if match:
            numbers.append(int(match.group(1)))
    next_num = max(numbers, default=0) + 1
    return f"{prefix}-{next_num:03d}"


def run(story_path: str) -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    config = load_config("chakra.yaml")
    story = Path(story_path).read_text().strip()
    story_title = story.split("\n")[0][:60]

    github = GitHubTool(os.environ["GITHUB_TOKEN"], config.github.repo)
    sheets = SheetsTool(
        config.google.credentials_path,
        config.google.spreadsheet_id,
        config.tracker.sheet_name,
    )
    agent = SDLCAgent(os.environ["ANTHROPIC_API_KEY"], config.anthropic.model)

    story_id = _next_story_id(config.story.id_prefix, sheets)
    logger.info("Starting SDLC loop: %s — %s", story_id, story_title)

    sheets.upsert_row(story_id, story_title, "overall", "Pending")

    # Planning phase
    sheets.update_status(story_id, "overall", "Planning")
    rejection_feedback = ""
    tasks = []
    for attempt in range(MAX_RETRIES):
        tasks = agent.plan(story, rejection_feedback=rejection_feedback)
        plan_text = "\n".join(
            f"  {i + 1}. {t['task']}: {t['description']}" for i, t in enumerate(tasks)
        )
        try:
            prompt_approval(f"Planning — {story_id}", plan_text)
            logger.info("Plan approved on attempt %d", attempt + 1)
            break
        except ApprovalRejected as e:
            rejection_feedback = e.reason
            logger.warning("Plan rejected (attempt %d/%d): %s", attempt + 1, MAX_RETRIES, e.reason)
            if attempt == MAX_RETRIES - 1:
                logger.error("Planning rejected %d times, aborting", MAX_RETRIES)
                sys.exit(1)

    # Coding phase
    sheets.update_status(story_id, "overall", "Coding")
    logger.info("Generating code for %d tasks", len(tasks))
    code_files = agent.code(story, tasks)

    # Testing phase with coverage enforcement
    sheets.update_status(story_id, "overall", "Testing")
    coverage_feedback = ""
    test_files: dict[str, str] = {}
    for attempt in range(MAX_RETRIES):
        test_files = agent.test(story, code_files, coverage_feedback=coverage_feedback)
        coverage, report = agent.measure_coverage(code_files, test_files)
        logger.info("Coverage attempt %d/%d: %.0f%%", attempt + 1, MAX_RETRIES, coverage)
        if coverage >= 95.0:
            break
        coverage_feedback = report
        if attempt == MAX_RETRIES - 1:
            logger.error(
                "Coverage %.0f%% below 95%% after %d retries, aborting",
                coverage,
                MAX_RETRIES,
            )
            sys.exit(1)

    # GitHub: branch, commit, PR
    branch_name = f"chakra/{story_id}-{_slugify(story_title)}"
    github.create_branch(branch_name, config.github.base_branch)
    all_files = {**code_files, **test_files}
    github.commit_files(branch_name, all_files, f"feat({story_id}): {story_title}")
    pr_url, pr_number = github.open_pr(
        branch_name,
        config.github.base_branch,
        f"[{story_id}] {story_title}",
        f"Generated by Chakra.\n\n**Story:**\n{story}\n\n**Tasks:**\n{plan_text}",
    )
    sheets.update_status(story_id, "overall", "PR Created")
    logger.info("PR opened: %s", pr_url)
    print(f"\nPR: {pr_url}")
    print("Waiting for PR to be merged...")

    # Wait for merge
    github.poll_merge(pr_number)

    # Trigger CI/CD and mark done
    github.trigger_cicd(config.github.ci_workflow, config.github.base_branch)
    sheets.update_status(story_id, "overall", "Done")
    logger.info("SDLC loop complete: %s", story_id)
    print(f"\nDone! {story_id} complete.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python orchestrator.py story.txt")
        sys.exit(1)
    run(sys.argv[1])
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_orchestrator.py -v
```

Expected: 8 passed

- [ ] **Step 5: Run full test suite with coverage**

```bash
pytest --cov=. --cov-report=term-missing -v
```

Expected: All tests pass. Coverage across `tools/` and `agents/` should be ≥ 95%.

- [ ] **Step 6: Commit**

```bash
git add orchestrator.py tests/test_orchestrator.py
git commit -m "feat: add orchestrator — full SDLC loop wired end-to-end"
```

---

## Task 9: Final Verification

- [ ] **Step 1: Run full test suite one final time**

```bash
pytest --cov=. --cov-report=term-missing -q
```

Expected: all tests pass, coverage ≥ 95% across all source files.

- [ ] **Step 2: Verify CLI usage message**

```bash
python orchestrator.py
```

Expected output:
```
Usage: python orchestrator.py story.txt
```

- [ ] **Step 3: Verify imports are clean**

```bash
python -c "from orchestrator import run; from agents.sdlc_agent import SDLCAgent; from tools.config import load_config; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Final commit**

```bash
git add docs/
git commit -m "docs: add phase 1 spec and implementation plan"
```
