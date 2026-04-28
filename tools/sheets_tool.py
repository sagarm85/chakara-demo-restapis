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
