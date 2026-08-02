import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

EMBEDDING_MODEL = "mistral-embed"

# What a book's page_content looks like, for semantic search quality.
BOOK_TEXT_TEMPLATE = "{name} by {author}. Category: {category}. Genre: {genre}. Edition: {edition}. Publication: {publication}."
