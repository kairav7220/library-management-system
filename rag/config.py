import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("RAG_DATA_DIR", BASE_DIR / "data"))

DATA_DIR.mkdir(parents=True, exist_ok=True)

EMBEDDING_MODEL = "mistral-embed"

# What a book's page_content looks like, for semantic search quality.
BOOK_TEXT_TEMPLATE = "{name} by {author}. Category: {category}. Genre: {genre}. Edition: {edition}. Publication: {publication}."
