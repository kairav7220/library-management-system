"""Persistent memory for conversation history.

Each turn stores the user message, the agent that handled it, the final
response, and which tools were invoked. History is reloaded at session start so
agents can recall prior conversations.

Backend is chosen at runtime:
- Postgres (Neon / Vercel) when DATABASE_URL is set — durable on serverless.
- SQLite file fallback otherwise (local dev).
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "chat_history.db"
DATABASE_URL = os.environ.get("DATABASE_URL")

CREATE_SQL_SQLITE = """
    CREATE TABLE IF NOT EXISTS chat_history (
        session_id   TEXT NOT NULL,
        user_message TEXT,
        agent_name   TEXT,
        agent_response TEXT,
        tool_calls   TEXT,
        created_at   TEXT
    )
"""

CREATE_SQL_POSTGRES = """
    CREATE TABLE IF NOT EXISTS chat_history (
        id           BIGSERIAL PRIMARY KEY,
        session_id   TEXT NOT NULL,
        user_message TEXT,
        agent_name   TEXT,
        agent_response TEXT,
        tool_calls   TEXT,
        created_at   TEXT
    )
"""


def _connect_sqlite() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(CREATE_SQL_SQLITE)
    return conn


def _connect_postgres():
    import psycopg
    from psycopg.rows import dict_row

    conn = psycopg.connect(DATABASE_URL)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(CREATE_SQL_POSTGRES)
    conn.commit()
    return conn


def _connect():
    if DATABASE_URL:
        return _connect_postgres()
    return _connect_sqlite()


def load_history(session_id: str, limit: int = 20) -> list:
    """Return prior messages for a session as LangChain message objects."""
    conn = _connect()
    try:
        if DATABASE_URL:
            from psycopg.rows import dict_row

            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT user_message, agent_response FROM chat_history
                    WHERE session_id = %s
                    ORDER BY id DESC LIMIT %s
                    """,
                    (session_id, limit),
                )
                rows = cur.fetchall()
        else:
            rows = conn.execute(
                """
                SELECT user_message, agent_response FROM chat_history
                WHERE session_id = ?
                ORDER BY rowid DESC LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
    finally:
        conn.close()
    messages = []
    for row in reversed(rows):
        if row["user_message"]:
            messages.append(HumanMessage(content=row["user_message"]))
        if row["agent_response"]:
            messages.append(AIMessage(content=row["agent_response"]))
    return messages


def append_turn(
    session_id: str,
    user_message: str,
    agent_name: str,
    agent_response: str,
    tool_calls: list = None,
) -> None:
    """Persist one completed conversation turn."""
    values = (
        session_id,
        user_message,
        agent_name,
        agent_response,
        json.dumps(tool_calls or []),
        datetime.now().isoformat(),
    )
    conn = _connect()
    try:
        if DATABASE_URL:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO chat_history
                        (session_id, user_message, agent_name, agent_response,
                         tool_calls, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    values,
                )
            conn.commit()
        else:
            conn.execute(
                """
                INSERT INTO chat_history
                    (session_id, user_message, agent_name, agent_response,
                     tool_calls, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                values,
            )
            conn.commit()
    finally:
        conn.close()
