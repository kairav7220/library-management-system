from langchain_core.tools import tool

from tools.gsheets_client import get_all_records, get_worksheet, next_row

SHEET = "User Table"
# User Table columns:
# row_num, user_id, user_type, username, password, email, phone, status


@tool
def add_user(user_data: list) -> dict:
    """Add a new user to the User Table.

    user_data is a list in order:
    [user_type, username, password, email, phone].
    row_num, user_id and status are auto-generated.
    """
    ws = get_worksheet(SHEET)
    nrow = next_row(SHEET)
    row_data = [f"=ROW()", f'="USER_"&A{nrow}-1'] + user_data + ["0"]
    ws.update([row_data], f"A{nrow}:H{nrow}", value_input_option="USER_ENTERED")
    return get_all_records(SHEET)[-1]


@tool
def get_user_by_id(user_id: str) -> dict | None:
    """Find an active user by their user_id (e.g. USER_1). Returns the user."""
    for row in get_all_records(SHEET):
        if row.get("user_id") == user_id:
            return row
    return None


@tool
def get_all_users() -> list[dict]:
    """Get all active users from the User Table."""
    return get_all_records(SHEET)


@tool
def delete_user(row_num: int) -> str:
    """Soft-delete a user by setting status to 1.

    Call this only AFTER the user has confirmed the deletion.
    """
    get_worksheet(SHEET).update_acell(f"H{row_num}", 1)
    return f"User at row {row_num} deleted."
