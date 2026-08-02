from langchain_core.tools import tool

from tools.gsheets_client import get_all_records, get_worksheet, next_row

SHEET = "Member Table"
# Member Table columns:
# row_num, mem_id, name, user_id, password, email, phone, user_row_num,
# permanent_address, temporary_address, status


@tool
def add_member(details: dict) -> dict:
    """Add a new member to the Member Table.

    details keys: name, user_id, password, email, phone, user_row_num,
    permanent_address, temporary_address. mem_id and status auto-generated.
    """
    ws = get_worksheet(SHEET)
    nrow = next_row(SHEET)
    row_data = [
        "=ROW()",
        f'="MEM_"&A{nrow}-1',
        details.get("name"),
        details.get("user_id"),
        details.get("password"),
        details.get("email"),
        details.get("phone"),
        details.get("user_row_num", ""),
        details.get("permanent_address"),
        details.get("temporary_address"),
        "0",
    ]
    ws.update([row_data], f"A{nrow}:K{nrow}", value_input_option="USER_ENTERED")
    return get_all_records(SHEET)[-1]


@tool
def update_member(row_num: int, details: dict) -> str:
    """Update an existing member by spreadsheet row number.

    details keys (any subset): name, user_id, password, email, phone,
    permanent_address, temporary_address.
    """
    ws = get_worksheet(SHEET)
    col_map = {
        "name": 3,
        "user_id": 4,
        "password": 5,
        "email": 6,
        "phone": 7,
        "permanent_address": 9,
        "temporary_address": 10,
    }
    for key, col in col_map.items():
        if key in details and details[key] is not None:
            ws.update_cell(row_num, col, details[key])
    return f"Member at row {row_num} updated."


@tool
def get_member_by_row_num(row_num: int) -> list:
    """Get a member's row by spreadsheet row number."""
    return get_worksheet(SHEET).get(f"A{row_num}:K{row_num}")


@tool
def get_member_by_id(mem_id: str) -> dict | None:
    """Find a member by their mem_id (e.g. MEM_1). Returns the member."""
    for row in get_all_records(SHEET):
        if row.get("mem_id") == mem_id:
            return row
    return None


@tool
def get_all_members() -> list[dict]:
    """Get all non-deleted members."""
    return get_all_records(SHEET)


@tool
def delete_member(row_num: int) -> str:
    """Soft-delete a member by setting status to 1.

    Call this only AFTER the user has confirmed the deletion.
    """
    get_worksheet(SHEET).update_acell(f"K{row_num}", 1)
    return f"Member at row {row_num} deleted."
