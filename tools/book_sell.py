from datetime import datetime

from langchain_core.tools import tool

from tools.gsheets_client import get_all_records, get_worksheet, next_row

SHEET = "Book Sell"
# Book Sell columns:
# row_num, order_id, order_date, timestamp, book_id, book_name,
# book_price, mem_id


@tool
def book_sell(details: dict) -> dict:
    """Record a book sale to a member.

    details keys: order_date, book_id, book_name, book_price, mem_id.
    order_id and timestamp auto-generated.
    """
    ws = get_worksheet(SHEET)
    nrow = next_row(SHEET)
    row_data = [
        "=ROW()",
        f'="ORDER_"&A{nrow}-1',
        details.get("order_date"),
        datetime.now().strftime("%d-%b-%Y %I:%M:%S %p"),
        details.get("book_id"),
        details.get("book_name"),
        details.get("book_price"),
        details.get("mem_id"),
    ]
    ws.update([row_data], f"A{nrow}:H{nrow}", value_input_option="USER_ENTERED")
    return get_all_records(SHEET)[-1]


@tool
def update_book_sell(row_num: int, details: dict) -> str:
    """Update an existing book sale by spreadsheet row number.

    details keys (any subset): order_date, book_id, book_name, book_price,
    mem_id.
    """
    ws = get_worksheet(SHEET)
    col_map = {
        "order_date": 3,
        "book_id": 5,
        "book_name": 6,
        "book_price": 7,
        "mem_id": 8,
    }
    for key, col in col_map.items():
        if key in details and details[key] is not None:
            ws.update_cell(row_num, col, details[key])
    return f"Book sell order at row {row_num} updated."


@tool
def get_all_book_sells() -> list[dict]:
    """Get all book sale records."""
    return get_all_records(SHEET)
