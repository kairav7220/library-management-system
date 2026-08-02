"""Catalog Librarian — manages the book collection, categories and genres."""

from langgraph.prebuilt import create_react_agent

from tools.book import (
    add_book,
    update_book,
    get_book_by_row_num,
    get_all_books,
    delete_book,
)
from tools.book_cat import (
    add_category,
    update_category,
    get_category_by_row_num,
    get_all_categories,
    get_books_by_category,
    delete_category,
)
from tools.book_genre import (
    add_book_genre,
    update_book_genre,
    get_book_genre_by_row_num,
    get_all_book_genres,
    delete_book_genre,
)
from tools.consult import consult_circulation

TOOLS = [
    add_book,
    update_book,
    get_book_by_row_num,
    get_all_books,
    delete_book,
    add_category,
    update_category,
    get_category_by_row_num,
    get_all_categories,
    get_books_by_category,
    delete_category,
    add_book_genre,
    update_book_genre,
    get_book_genre_by_row_num,
    get_all_book_genres,
    delete_book_genre,
    consult_circulation,
]

SYSTEM_PROMPT = """You are the Catalog Librarian of the library. You are meticulous,
organized, and obsessed with proper classification. You think in taxonomies and metadata.

Your responsibilities:
- Maintain the book collection (Book Table): add books, edit their details,
  and soft-delete books.
- Manage Book Categories: create, edit, and delete categories. Books belong
  to exactly one category.
- Manage Book Genres: create, edit, and delete genres.
- Answer questions about the catalog: what books exist, by whom, in which
  category or genre.

Guidelines:
- When the user asks to add or edit a book, fill in every field you know and
  leave missing fields blank — never invent data the user did not give you.
- Deletes are special: ALWAYS confirm with the user before calling any
  delete_* tool. Ask 'Are you sure you want to delete X? This hides it from
  the catalog.' Only delete after the user explicitly says yes.
- You do NOT handle issuing books, returns, sales, members, subscriptions,
  or payments. Refer those to the Director.
- Be concise and helpful. When you add or edit something, confirm what you did.
"""


def create_catalog_agent(llm):
    return create_react_agent(
        model=llm,
        tools=TOOLS,
        name="Catalog Librarian",
        prompt=SYSTEM_PROMPT,
    )
