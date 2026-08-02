from langchain_core.tools import tool

from tools.gsheets_client import get_all_records, get_worksheet, next_row

SHEET = "Book Category"
# Book Category columns:
# row_num, cat_id, cat_name, description, book_names, status


@tool
def add_category(details: dict) -> dict:
    """Add a new book category.

    details keys: cat_name, description, book_names (comma-separated list).
    ID and status are auto-generated.
    """
    ws = get_worksheet(SHEET)
    nrow = next_row(SHEET)
    row_data = [
        "=ROW()",
        f'="CAT_"&A{nrow}-1',
        details.get("cat_name"),
        details.get("description"),
        details.get("book_names"),
        "0",
    ]
    ws.update([row_data], f"A{nrow}:F{nrow}", value_input_option="USER_ENTERED")
    return get_all_records(SHEET)[-1]


@tool
def update_category(row_num: int, details: dict) -> str:
    """Update an existing category by spreadsheet row number.

    details keys (any subset): cat_name, description, book_names.
    """
    ws = get_worksheet(SHEET)
    col_map = {"cat_name": 3, "description": 4, "book_names": 5}
    for key, col in col_map.items():
        if key in details and details[key] is not None:
            ws.update_cell(row_num, col, details[key])
    return f"Category at row {row_num} updated."


@tool
def get_category_by_row_num(row_num: int) -> list:
    """Get a category's row by spreadsheet row number."""
    return get_worksheet(SHEET).get(f"A{row_num}:E{row_num}")


@tool
def get_all_categories() -> list[dict]:
    """Get all non-deleted book categories."""
    return get_all_records(SHEET)


@tool
def get_books_by_category(cat_name: str) -> list:
    """Get the list of book names belonging to a category by name."""
    all_values = get_worksheet(SHEET).get_all_values()
    books = [row[4] for row in all_values[1:] if row[2] == cat_name and row[5] != "1"]
    return books


@tool
def delete_category(row_num: int) -> str:
    """Soft-delete a category by setting status to 1.

    Call this only AFTER the user has confirmed the deletion.
    """
    get_worksheet(SHEET).update_acell(f"F{row_num}", 1)
    return f"Category at row {row_num} deleted."
