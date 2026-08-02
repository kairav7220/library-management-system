"""Book embedder — index and search books via pgvector on Neon Postgres."""

import json
import os

from langchain_core.documents import Document
from langchain_mistralai import MistralAIEmbeddings

from rag.config import EMBEDDING_MODEL
from rag.loader import load_books

DATABASE_URL = os.environ.get("DATABASE_URL")

_embeddings = None


def get_embeddings() -> MistralAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = MistralAIEmbeddings(model=EMBEDDING_MODEL)
    return _embeddings


def _embed(texts: list[str]) -> list[list[float]]:
    return get_embeddings().embed_documents(texts)


def _connect_pg():
    import psycopg
    from pgvector.psycopg import register_vector

    conn = psycopg.connect(DATABASE_URL)
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cur.execute("SELECT atttypmod FROM pg_attribute WHERE attrelid = 'book_embeddings'::regclass AND attname = 'embedding'")
        row = cur.fetchone()
        if row and row[0] != 1024:
            cur.execute("DROP TABLE book_embeddings")
            row = None
        if row is None:
            cur.execute(
                """
                CREATE TABLE book_embeddings (
                    id        BIGSERIAL PRIMARY KEY,
                    content   TEXT NOT NULL,
                    metadata  JSONB,
                    embedding vector(1024)
                )
                """
            )
    conn.commit()
    register_vector(conn)
    return conn


def _vec(vec: list[float]):
    from pgvector.psycopg.vector import Vector

    return Vector(vec)


def index_all() -> None:
    """(Re)build the book collection from current sheet data."""
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is required for RAG indexing")
    docs = load_books()
    conn = _connect_pg()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM book_embeddings")
        if docs:
            texts = [d.page_content for d in docs]
            vecs = _embed(texts)
            with conn.cursor() as cur:
                for d, vec in zip(docs, vecs):
                    cur.execute(
                        """
                        INSERT INTO book_embeddings (content, metadata, embedding)
                        VALUES (%s, %s, %s)
                        """,
                        (d.page_content, json.dumps(d.metadata), _vec(vec)),
                    )
        conn.commit()
    finally:
        conn.close()


def search_books(query: str, k: int = 5) -> list[dict]:
    """Semantic search over the book catalog. Returns doc + score dicts."""
    if not DATABASE_URL:
        return []
    conn = _connect_pg()
    try:
        vec = _vec(_embed([query])[0])
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT content, metadata, 1 - (embedding <=> %s) AS score
                FROM book_embeddings
                ORDER BY embedding <=> %s
                LIMIT %s
                """,
                (vec, vec, k),
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    out = []
    for content, meta, score in rows:
        out.append({"content": content, "metadata": meta, "score": float(score)})
    return out
