from langchain_core.tools import tool

from tools.gsheets_client import get_all_records, get_worksheet, next_row

SHEET = "Book Genre"
# Book Genre columns:
# row_num, genre_id, genre_title, book_names, status


@tool
def add_book_genre(details: dict) -> dict:
    """Add a new book genre.

    details keys: genre_title, book_names (comma-separated list).
    ID and status are auto-generated.
    """
    ws = get_worksheet(SHEET)
    nrow = next_row(SHEET)
    row_data = [
        "=ROW()",
        f'="GENRE_"&A{nrow}-1',
        details.get("genre_title"),
        details.get("book_names"),
        "0",
    ]
    ws.update([row_data], f"A{nrow}:E{nrow}", value_input_option="USER_ENTERED")
    return get_all_records(SHEET)[-1]


@tool
def update_book_genre(row_num: int, details: dict) -> str:
    """Update an existing genre by spreadsheet row number.

    details keys (any subset): genre_title, book_names.
    """
    ws = get_worksheet(SHEET)
    col_map = {"genre_title": 3, "book_names": 4}
    for key, col in col_map.items():
        if key in details and details[key] is not None:
            ws.update_cell(row_num, col, details[key])
    return f"Genre at row {row_num} updated."


@tool
def get_book_genre_by_row_num(row_num: int) -> list:
    """Get a genre's row by spreadsheet row number."""
    return get_worksheet(SHEET).get(f"A{row_num}:E{row_num}")


@tool
def get_all_book_genres() -> list[dict]:
    """Get all non-deleted book genres."""
    return get_all_records(SHEET)


@tool
def delete_book_genre(row_num: int) -> str:
    """Soft-delete a genre by setting status to 1.

    Call this only AFTER the user has confirmed the deletion.
    """
    get_worksheet(SHEET).update_acell(f"E{row_num}", 1)
    return f"Genre at row {row_num} deleted."
