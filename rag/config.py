import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("RAG_DATA_DIR", BASE_DIR / "data"))
CHROMA_DIR = Path(os.environ.get("CHROMA_DIR", BASE_DIR / "data" / "chroma_db"))

DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_BOOKS = "library_books"

# What a book's page_content looks like, for semantic search quality.
BOOK_TEXT_TEMPLATE = "{name} by {author}. Category: {category}. Genre: {genre}. Edition: {edition}. Publication: {publication}."
