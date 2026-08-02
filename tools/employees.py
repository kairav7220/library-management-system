from langchain_core.tools import tool

from tools.gsheets_client import get_all_records, get_worksheet, next_row

SHEET = "Employee Table"
# Employee Table columns:
# row_num, emp_id, name, user_id, password, email, phone, designation,
# salary, user_row_num, permanent_address, temporary_address, status


@tool
def add_employee(details: dict) -> dict:
    """Add a new employee to the Employee Table.

    details keys: name, user_id, password, email, phone, designation,
    salary, user_row_num, permanent_address, temporary_address.
    emp_id and status auto-generated.
    """
    ws = get_worksheet(SHEET)
    nrow = next_row(SHEET)
    row_data = [
        "=ROW()",
        f'="EMP_"&A{nrow}-1',
        details.get("name"),
        details.get("user_id"),
        details.get("password"),
        details.get("email"),
        details.get("phone"),
        details.get("designation"),
        details.get("salary"),
        details.get("user_row_num", ""),
        details.get("permanent_address"),
        details.get("temporary_address"),
        "0",
    ]
    ws.update([row_data], f"A{nrow}:M{nrow}", value_input_option="USER_ENTERED")
    return get_all_records(SHEET)[-1]


@tool
def update_employee(row_num: int, details: dict) -> str:
    """Update an existing employee by spreadsheet row number.

    details keys (any subset): name, user_id, password, email, phone,
    designation, salary, permanent_address, temporary_address.
    """
    ws = get_worksheet(SHEET)
    col_map = {
        "name": 3,
        "user_id": 4,
        "password": 5,
        "email": 6,
        "phone": 7,
        "designation": 8,
        "salary": 9,
        "permanent_address": 11,
        "temporary_address": 12,
    }
    for key, col in col_map.items():
        if key in details and details[key] is not None:
            ws.update_cell(row_num, col, details[key])
    return f"Employee at row {row_num} updated."


@tool
def get_employee_by_row_num(row_num: int) -> list:
    """Get an employee's row by spreadsheet row number."""
    return get_worksheet(SHEET).get(f"A{row_num}:M{row_num}")


@tool
def get_employee_by_id(emp_id: str) -> dict | None:
    """Find an employee by their emp_id (e.g. EMP_1). Returns the employee."""
    for row in get_all_records(SHEET):
        if row.get("emp_id") == emp_id:
            return row
    return None


@tool
def get_all_employees() -> list[dict]:
    """Get all non-deleted employees."""
    return get_all_records(SHEET)


@tool
def delete_employee(row_num: int) -> str:
    """Soft-delete an employee by setting status to 1.

    Call this only AFTER the user has confirmed the deletion.
    """
    get_worksheet(SHEET).update_acell(f"M{row_num}", 1)
    return f"Employee at row {row_num} deleted."
