"""Peer-to-peer consultation tools — agents can query each other."""

from langchain_core.tools import tool

from tools.members import get_member_by_id
from tools.book import get_all_books
from tools.book_issue import get_all_issues


@tool
def consult_membership(mem_id: str) -> dict:
    """Ask Membership Services whether a member exists and is active.

    Used by other agents (e.g. Circulation) to validate a member before
    issuing a book. Returns the member record or None.
    """
    return get_member_by_id.invoke({"mem_id": mem_id})


@tool
def consult_catalog(query: str) -> list[dict]:
    """Ask the Catalog Librarian to look up books in the catalog.

    Returns a list of books whose name or author contains the query string.
    """
    books = get_all_books.invoke({})
    q = query.lower()
    return [b for b in books if q in (b.get("book_name") or "").lower() or q in (b.get("book_author") or "").lower()]


@tool
def consult_circulation(book_id: str) -> list[dict]:
    """Ask the Circulation Librarian which issues exist for a book.

    Returns all issue records matching the book_id.
    """
    issues = get_all_issues.invoke({})
    return [i for i in issues if i.get("book_id") == book_id]
