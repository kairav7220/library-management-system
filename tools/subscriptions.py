from datetime import datetime

from langchain_core.tools import tool

from tools.gsheets_client import get_all_records, get_worksheet, next_row

SHEET = "Subscription Table"
# Subscription Table columns:
# row_num, transaction_id, transaction_date, timestamp, plan_mode, mem_id,
# mem_subscription_amount, plan_type, plan_start, plan_end, subscription_status


@tool
def add_subscription(details: dict) -> dict:
    """Add a new subscription plan for a member.

    details keys: plan_mode (online/offline), mem_id, mem_subscription_amount,
    plan_type (Annual/Monthly), plan_start, plan_end.
    transaction_id, dates and timestamp auto-generated.
    """
    ws = get_worksheet(SHEET)
    nrow = next_row(SHEET)
    row_data = [
        "=ROW()",
        f'="TXN_"&A{nrow}-1',
        datetime.now().strftime("%d-%b-%Y"),
        datetime.now().strftime("%I:%M:%S %p"),
        details.get("plan_mode"),
        details.get("mem_id"),
        details.get("mem_subscription_amount"),
        details.get("plan_type"),
        details.get("plan_start"),
        details.get("plan_end"),
        "0",
    ]
    ws.update([row_data], f"A{nrow}:K{nrow}", value_input_option="USER_ENTERED")
    return get_all_records(SHEET)[-1]


@tool
def update_subscription(row_num: int, details: dict) -> str:
    """Update an existing subscription by spreadsheet row number.

    details keys (any subset): plan_mode, mem_id, mem_subscription_amount,
    plan_type, plan_start, plan_end, subscription_status.
    """
    ws = get_worksheet(SHEET)
    col_map = {
        "plan_mode": 5,
        "mem_id": 6,
        "mem_subscription_amount": 7,
        "plan_type": 8,
        "plan_start": 9,
        "plan_end": 10,
        "subscription_status": 11,
    }
    for key, col in col_map.items():
        if key in details and details[key] is not None:
            ws.update_cell(row_num, col, details[key])
    return f"Subscription at row {row_num} updated."


@tool
def get_subscription_by_row_num(row_num: int) -> list:
    """Get a subscription row by spreadsheet row number."""
    return get_worksheet(SHEET).get(f"A{row_num}:K{row_num}")


@tool
def get_all_subscriptions() -> list[dict]:
    """Get all non-deleted subscriptions."""
    return get_all_records(SHEET)


@tool
def delete_subscription(row_num: int) -> str:
    """Soft-delete a subscription by setting status to 1.

    Call this only AFTER the user has confirmed the deletion.
    """
    get_worksheet(SHEET).update_acell(f"K{row_num}", 1)
    return f"Subscription at row {row_num} deleted."
