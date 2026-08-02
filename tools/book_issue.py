from datetime import datetime

from langchain_core.tools import tool

from tools.gsheets_client import get_all_records, get_worksheet, next_row

SHEET = "Book Issue"
# Book Issue columns:
# row_num, transaction_id, transaction_date, timestamp, book_id, issued_date,
# issued_to, recieved_by, returned_date


@tool
def book_issue(details: dict) -> dict:
    """Issue a book to a member.

    details keys: book_id, mem_id (the member ID), issued_date,
    transaction_date (optional, defaults to today), recieved_by (optional,
    employee ID).
    transaction_id and timestamp are auto-generated.
    """
    ws = get_worksheet(SHEET)
    nrow = next_row(SHEET)
    row_data = [
        "=ROW()",
        f'="TXN_"&A{nrow}-1',
        details.get("transaction_date") or datetime.now().strftime("%d-%b-%Y"),
        datetime.now().strftime("%d-%b-%Y %I:%M:%S %p"),
        details.get("book_id"),
        details.get("issued_date"),
        details.get("mem_id"),
        details.get("recieved_by", ""),
        details.get("returned_date", ""),
    ]
    ws.update([row_data], f"A{nrow}:I{nrow}", value_input_option="USER_ENTERED")
    return get_all_records(SHEET)[-1]


@tool
def book_return(row_num: int, details: dict) -> str:
    """Process a book return.

    details keys: recieved_by (employee ID), returned_date.
    """
    ws = get_worksheet(SHEET)
    values = [[details.get("recieved_by"), details.get("returned_date")]]
    ws.update(values, f"H{row_num}:I{row_num}", value_input_option="USER_ENTERED")
    return f"Book issue at row {row_num} marked as returned."


@tool
def get_issue_by_row_num(row_num: int) -> list:
    """Get a book issue/return row by spreadsheet row number."""
    return get_worksheet(SHEET).get(f"A{row_num}:I{row_num}")


@tool
def get_all_issues() -> list[dict]:
    """Get all book issue records."""
    return get_all_records(SHEET)
