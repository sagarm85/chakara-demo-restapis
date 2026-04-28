import pytest
from unittest.mock import MagicMock, patch
from tools.sheets_tool import SheetsTool


@pytest.fixture
def mock_worksheet():
    ws = MagicMock()
    ws.get_all_records.return_value = []
    return ws


@pytest.fixture
def sheets_tool(mock_worksheet):
    with patch("tools.sheets_tool.gspread") as mock_gspread, \
         patch("tools.sheets_tool.Credentials"):
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
    sheets_tool.upsert_row("CHAKRA-001", "Add login", "overall", "Pending")
    mock_worksheet.append_row.assert_called_once()
    row = mock_worksheet.append_row.call_args[0][0]
    assert row[0] == "CHAKRA-001"
    assert row[1] == "Add login"
    assert row[2] == "overall"
    assert row[3] == "Pending"


def test_upsert_row_updates_existing_row(sheets_tool, mock_worksheet):
    mock_worksheet.get_all_records.return_value = [
        {"Story ID": "CHAKRA-001", "Story Title": "Add login", "Task": "overall",
         "Status": "Pending", "Updated At": "old"}
    ]
    sheets_tool.upsert_row("CHAKRA-001", "Add login", "overall", "Coding")
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
    assert "UTC" in col_5_calls[0][0][2]


def test_update_status_row_not_found_logs_warning(sheets_tool, mock_worksheet, caplog):
    import logging
    mock_worksheet.get_all_records.return_value = []
    with caplog.at_level(logging.WARNING):
        sheets_tool.update_status("CHAKRA-999", "overall", "Done")
    assert "not found" in caplog.text.lower()


def test_get_all_story_ids_returns_ids(sheets_tool, mock_worksheet):
    mock_worksheet.get_all_records.return_value = [
        {"Story ID": "CHAKRA-001", "Story Title": "A", "Task": "overall", "Status": "Done", "Updated At": "x"},
        {"Story ID": "CHAKRA-002", "Story Title": "B", "Task": "overall", "Status": "Done", "Updated At": "x"},
    ]
    ids = sheets_tool.get_all_story_ids()
    assert ids == ["CHAKRA-001", "CHAKRA-002"]


def test_get_all_story_ids_empty_sheet(sheets_tool, mock_worksheet):
    mock_worksheet.get_all_records.return_value = []
    assert sheets_tool.get_all_story_ids() == []


def test_get_or_create_sheet_creates_when_not_found():
    """Cover the WorksheetNotFound branch in _get_or_create_sheet (lines 23-26)."""
    import gspread as _gspread
    new_ws = MagicMock()
    with patch("tools.sheets_tool.gspread") as mock_gspread, \
         patch("tools.sheets_tool.Credentials"):
        mock_client = MagicMock()
        mock_gspread.authorize.return_value = mock_client
        mock_gspread.WorksheetNotFound = _gspread.WorksheetNotFound
        mock_spreadsheet = MagicMock()
        mock_client.open_by_key.return_value = mock_spreadsheet
        # First call raises, second call (add_worksheet) returns new_ws
        mock_spreadsheet.worksheet.side_effect = _gspread.WorksheetNotFound
        mock_spreadsheet.add_worksheet.return_value = new_ws
        tool = SheetsTool("./credentials.json", "sheet-id-abc", "New Sheet")
    assert tool._sheet is new_ws
    mock_spreadsheet.add_worksheet.assert_called_once_with("New Sheet", rows=1000, cols=5)
    new_ws.append_row.assert_called_once()
