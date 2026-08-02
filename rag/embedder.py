"""Book embedder — index and search books.

Backend chosen at runtime:
- Postgres + pgvector when DATABASE_URL is set (durable on serverless).
- ChromaDB local file fallback otherwise (local dev).
"""

import json
import os

import chromadb
from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer

from rag.config import CHROMA_DIR, COLLECTION_BOOKS, EMBEDDING_MODEL
from rag.loader import load_books

DATABASE_URL = os.environ.get("DATABASE_URL")
VECTOR_DIMS = 384  # all-MiniLM-L6-v2 output size

_client = None
_model = None


def _get_client() -> chromadb.Client:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _client


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def _embed(texts: list[str]) -> list[list[float]]:
    vecs = get_model().encode(texts)
    return [v.tolist() for v in vecs]


def _connect_pg():
    import psycopg
    from pgvector.psycopg import register_vector

    conn = psycopg.connect(DATABASE_URL)
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS book_embeddings (
                id        BIGSERIAL PRIMARY KEY,
                content   TEXT NOT NULL,
                metadata  JSONB,
                embedding vector(384)
            )
            """
        )
    conn.commit()
    register_vector(conn)
    return conn


def _vec(vec: list[float]):
    from pgvector.psycopg.vector import Vector

    return Vector(vec)


def _index_documents_chroma(collection_name: str, docs: list[Document]):
    coll = _get_client().get_or_create_collection(
        collection_name, metadata={"hnsw:space": "cosine"}
    )
    if coll.count() > 0:
        coll.delete(ids=coll.get()["ids"])
    if not docs:
        return coll
    ids = []
    texts = []
    metadatas = []
    for i, d in enumerate(docs):
        ids.append(f"{collection_name}_{i}")
        texts.append(d.page_content)
        metadatas.append(d.metadata)
    coll.upsert(
        ids=ids,
        embeddings=_embed(texts),
        documents=texts,
        metadatas=metadatas,
    )
    return coll


def _index_pg(docs: list[Document]) -> None:
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


def index_all() -> None:
    """(Re)build the book collection from current sheet data."""
    docs = load_books()
    if DATABASE_URL:
        _index_pg(docs)
    else:
        _index_documents_chroma(COLLECTION_BOOKS, docs)


def _search_chroma(query: str, k: int) -> list[dict]:
    coll = _get_client().get_or_create_collection(
        COLLECTION_BOOKS, metadata={"hnsw:space": "cosine"}
    )
    if coll.count() == 0:
        return []
    query_vec = _embed([query])
    results = coll.query(query_embeddings=query_vec, n_results=k)
    out = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]
    for doc, meta, dist in zip(docs, metas, dists):
        out.append({"content": doc, "metadata": meta, "score": 1 - dist})
    return out


def _search_pg(query: str, k: int) -> list[dict]:
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


def search_books(query: str, k: int = 5) -> list[dict]:
    """Semantic search over the book catalog. Returns doc + score dicts."""
    if DATABASE_URL:
        return _search_pg(query, k)
    return _search_chroma(query, k)
