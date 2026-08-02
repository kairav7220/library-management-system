import json
import os
import time

import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

load_dotenv()

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
]

# Google Sheets quota: 300 read requests/min, 60 write requests/min per user.
# Retry with backoff when we hit the limit.
MAX_RETRIES = 5
RETRY_DELAY = 1.0

SHEET_NAMES = [
    "User Table",
    "Book Table",
    "Book Category",
    "Book Genre",
    "Member Table",
    "Employee Table",
    "Subscription Table",
    "Payment Table",
    "Book Sell",
    "Book Issue",
]

# Column where the soft-delete flag lives (status == '1' means deleted)
STATUS_COL = {
    "User Table": 8,
    "Book Table": 10,
    "Book Category": 6,
    "Book Genre": 5,
    "Member Table": 11,
    "Employee Table": 13,
    "Subscription Table": 11,
    "Payment Table": None,
    "Book Sell": None,
    "Book Issue": None,
}

_client = None
_spreadsheet = None


def _retry(fn, *args, **kwargs):
    """Run a gspread call with retry + backoff on 429 rate limits."""
    delay = RETRY_DELAY
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            return fn(*args, **kwargs)
        except gspread.exceptions.APIError as e:
            last_exc = e
            if "429" in str(e) and attempt < MAX_RETRIES - 1:
                time.sleep(delay)
                delay *= 2
            else:
                raise
    raise last_exc


def get_client() -> gspread.Client:
    global _client
    if _client is not None:
        return _client
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if creds_json:
        creds_dict = json.loads(creds_json)
        credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    else:
        creds_path = os.environ.get("GOOGLE_SHEETS_CREDS_PATH")
        path = creds_path if creds_path else "credentials.json"
        credentials = Credentials.from_service_account_file(path, scopes=SCOPE)
    _client = gspread.authorize(credentials)
    return _client


def get_spreadsheet():
    global _spreadsheet
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise ValueError("GOOGLE_SHEET_ID is not set. Add it to .env or Vercel env vars.")
    if _spreadsheet is None:
        _spreadsheet = _retry(get_client().open_by_key, sheet_id)
    return _spreadsheet


def get_worksheet(sheet_name: str):
    if sheet_name not in SHEET_NAMES:
        raise ValueError(f"Unknown sheet '{sheet_name}'. Valid: {SHEET_NAMES}")
    return _retry(get_spreadsheet().worksheet, sheet_name)


def get_headers(sheet_name: str) -> list[str]:
    return _retry(get_worksheet(sheet_name).row_values, 1)


def get_all_records(sheet_name: str) -> list[dict]:
    values = _retry(get_worksheet(sheet_name).get_all_values)
    if not values:
        return []
    headers = values[0]
    records = []
    status_col = STATUS_COL.get(sheet_name)
    for i, row in enumerate(values[1:], start=2):
        if status_col is not None and len(row) >= status_col and row[status_col - 1] == "1":
            continue
        rec = {headers[j]: row[j] for j in range(min(len(headers), len(row)))}
        rec["_sheet_row"] = i
        records.append(rec)
    return records


def next_row(sheet_name: str) -> int:
    return len(_retry(get_worksheet(sheet_name).get_all_values)) + 1