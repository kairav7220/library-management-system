from datetime import datetime

from langchain_core.tools import tool

from tools.gsheets_client import get_all_records, get_worksheet, next_row

SHEET = "Payment Table"
# Payment Table columns:
# row_num, transaction_id, transaction_date, timestamp, payment_amount,
# payment_type, payment_mode, payment_status, paid_by, recieved_by, user_row_num


@tool
def add_payment(details: dict) -> dict:
    """Add a new payment record.

    details keys: payment_amount, payment_type, payment_mode, payment_status,
    paid_by (member ID), recieved_by (employee ID), user_row_num.
    transaction_id, dates and timestamp auto-generated.
    """
    ws = get_worksheet(SHEET)
    nrow = next_row(SHEET)
    row_data = [
        "=ROW()",
        f'="TXN_"&A{nrow}-1',
        datetime.now().strftime("%d-%b-%Y"),
        datetime.now().strftime("%I:%M:%S %p"),
        details.get("payment_amount"),
        details.get("payment_type"),
        details.get("payment_mode"),
        details.get("payment_status"),
        details.get("paid_by"),
        details.get("recieved_by"),
        details.get("user_row_num", ""),
    ]
    ws.update([row_data], f"A{nrow}:K{nrow}", value_input_option="USER_ENTERED")
    return get_all_records(SHEET)[-1]


@tool
def get_payment_by_row_num(row_num: int) -> list:
    """Get a payment row by spreadsheet row number."""
    return get_worksheet(SHEET).get(f"A{row_num}:K{row_num}")


@tool
def get_all_payments() -> list[dict]:
    """Get all payment records."""
    return get_all_records(SHEET)
