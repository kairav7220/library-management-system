"""Shared state for the orchestration graph."""

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    # Conversation history shared across agents.
    messages: Annotated[list[BaseMessage], add_messages]
    # Which agent should handle this turn (set by the Director).
    next: str
    # Shared context (member data, book data, results, etc.).
    context: dict
    # Intermediate results for multi-step flows.
    scratchpad: str
    # Conversation session id (for persistent memory).
    session_id: str
