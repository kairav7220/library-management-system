"""RAG search tools — semantic search over books (pgvector or ChromaDB)."""

from langchain_core.tools import tool

from rag.embedder import index_all, search_books


@tool
def reindex_books() -> str:
    """Rebuild the semantic book index from the current Book Table.

    Call this AFTER adding, editing, or deleting a book so the Reference
    Librarian can find the latest catalog. Safe to call any time.
    """
    try:
        index_all()
        return "Book index rebuilt from the current catalog."
    except Exception as e:
        return f"Indexing failed: {e}"


@tool
def search_books_rag(query: str) -> str:
    """Search the book collection semantically.

    Good for natural-language queries like 'books about space',
    'fantasy novels', or 'something by Gibson'. Returns matching books
    with title, author, category and genre.
    """
    results = search_books(query)
    if not results:
        return "The catalog is not indexed yet. Run the indexer first."
    lines = []
    for r in results:
        m = r["metadata"]
        lines.append(
            f"- {m.get('name')} by {m.get('author')} "
            f"[{m.get('category')} / {m.get('genre')}] (score {r['score']:.2f})"
        )
    return "\n".join(lines)
