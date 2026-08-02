from langchain_core.tools import tool

from tools.gsheets_client import get_all_records, get_worksheet, next_row

SHEET = "Book Table"
# Book Table columns:
# row_num, book_id, book_name, book_author, book_price, book_cat,
# book_genre, edition, publication, status


def _reindex_after():
    """Rebuild the semantic book index (pgvector) after a write.
    Best-effort: never fails the underlying write if indexing hiccups."""
    try:
        from rag.embedder import index_all

        index_all()
    except Exception as e:
        print(f"[book.py] reindex failed: {e}")


@tool
def add_book(details: dict) -> dict:
    """Add a new book to the Book Table.

    details keys: book_name, book_author, book_price, book_cat,
    book_genre, edition, publication. IDs and status are auto-generated.
    """
    ws = get_worksheet(SHEET)
    nrow = next_row(SHEET)
    row_data = [
        "=ROW()",
        f'="BOOK_"&A{nrow}-1',
        details.get("book_name"),
        details.get("book_author"),
        details.get("book_price"),
        details.get("book_cat"),
        details.get("book_genre"),
        details.get("edition"),
        details.get("publication"),
        "0",
    ]
    ws.update([row_data], f"A{nrow}:J{nrow}", value_input_option="USER_ENTERED")
    _reindex_after()
    return get_all_records(SHEET)[-1]


@tool
def update_book(row_num: int, details: dict) -> str:
    """Update an existing book by its spreadsheet row number.

    details keys (any subset): book_name, book_author, book_price, book_cat,
    book_genre, edition, publication.
    """
    ws = get_worksheet(SHEET)
    col_map = {
        "book_name": 3,
        "book_author": 4,
        "book_price": 5,
        "book_cat": 6,
        "book_genre": 7,
        "edition": 8,
        "publication": 9,
    }
    for key, col in col_map.items():
        if key in details and details[key] is not None:
            ws.update_cell(row_num, col, details[key])
    _reindex_after()
    return f"Book at row {row_num} updated."


@tool
def get_book_by_row_num(row_num: int) -> list:
    """Get a book's row by its spreadsheet row number."""
    return get_worksheet(SHEET).get(f"A{row_num}:J{row_num}")


@tool
def get_all_books() -> list[dict]:
    """Get all non-deleted books from the Book Table."""
    return get_all_records(SHEET)


@tool
def delete_book(row_num: int) -> str:
    """Soft-delete a book by setting its status to 1 (hides from catalog).

    Call this only AFTER the user has confirmed the deletion.
    """
    get_worksheet(SHEET).update_acell(f"J{row_num}", 1)
    _reindex_after()
    return f"Book at row {row_num} deleted."
