"""Graph orchestration: Director classifies intent and routes to specialists.

The Director is a lightweight routing node backed by an LCEL
intent-classification chain (structured output). It does not emit an assistant
message; only the routed specialist produces the answer. The Director react
agent is only invoked when the request should be handled directly (reports,
overviews, ambiguous).
"""

from typing import Literal

from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langgraph.graph import START, END, StateGraph
from pydantic import BaseModel, Field

from agents.catalog_agent import create_catalog_agent
from agents.circulation_agent import create_circulation_agent
from agents.director_agent import create_director_agent
from agents.membership_agent import create_membership_agent
from agents.reference_agent import create_reference_agent
from graph.state import AgentState
from graph.subgraphs import route_continuation
from tools.llm import get_llm

AGENTS = {
    "Catalog Librarian": "catalog",
    "Circulation Librarian": "circulation",
    "Membership Services": "membership",
    "Reference Librarian": "reference",
    "Library Director": "director",
}

CLASSIFIER_PROMPT = """You are the routing layer of a library management system.
Read the user's latest message and decide which librarian should handle it.

- Catalog Librarian: adding/editing/deleting books, categories, genres; book
  catalog management.
- Circulation Librarian: issuing books, returning books, recording book sales.
- Membership Services: registering members or employees, subscriptions,
  payments.
- Reference Librarian: finding books about a topic, recommendations, questions
  about the collection (read-only).
- Library Director: statistics, reports, overviews, greetings, ambiguous or
  out-of-scope requests.

Conversation so far:
{history}

Latest user message:
{message}
"""


class RouteDecision(BaseModel):
    next_agent: Literal[
        "Catalog Librarian",
        "Circulation Librarian",
        "Membership Services",
        "Reference Librarian",
        "Library Director",
    ] = Field(description="The librarian agent that should handle this request")
    reason: str = Field(description="Short justification for the routing choice")


def build_classifier(llm) -> Runnable:
    prompt = ChatPromptTemplate.from_template(CLASSIFIER_PROMPT)
    return prompt | llm.with_structured_output(RouteDecision)


def _last_user_turn(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Return messages up to and including the last human message, so a
    sub-agent never receives a trailing assistant message (Mistral rejects
    that ordering)."""
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].type == "human":
            return messages[: i + 1]
    return messages


def build_graph(llm=None, classifier=None):
    llm = llm or get_llm()
    classifier = classifier or build_classifier(llm)

    catalog = create_catalog_agent(llm)
    circulation = create_circulation_agent(llm)
    membership = create_membership_agent(llm)
    reference = create_reference_agent(llm)
    director = create_director_agent(llm)

    def _run(agent, name, state: AgentState) -> dict:
        result = agent.invoke({"messages": _last_user_turn(state["messages"])})
        return {"messages": result["messages"], "next": name}

    def run_catalog(state):
        return _run(catalog, "Catalog Librarian", state)

    def run_circulation(state):
        return _run(circulation, "Circulation Librarian", state)

    def run_membership(state):
        return _run(membership, "Membership Services", state)

    def run_reference(state):
        return _run(reference, "Reference Librarian", state)

    def run_director(state):
        return _run(director, "Library Director", state)

    def classify(state: AgentState) -> dict:
        continuation = route_continuation(
            state["messages"], state["messages"][-1].content
        )
        if continuation:
            return {"next": continuation}
        history = "\n".join(
            f"{'User' if m.type == 'human' else 'Agent'}: {m.content}"
            for m in state["messages"][-6:]
            if m.content
        )
        decision = classifier.invoke(
            {
                "history": history,
                "message": state["messages"][-1].content,
            }
        )
        return {"next": decision.next_agent}

    builder = StateGraph(AgentState)
    builder.add_node("classify", classify)
    builder.add_node("director", run_director)
    builder.add_node("catalog", run_catalog)
    builder.add_node("circulation", run_circulation)
    builder.add_node("membership", run_membership)
    builder.add_node("reference", run_reference)

    builder.add_edge(START, "classify")
    builder.add_conditional_edges(
        "classify",
        lambda state: AGENTS.get(state.get("next"), "director"),
        {
            "catalog": "catalog",
            "circulation": "circulation",
            "membership": "membership",
            "reference": "reference",
            "director": "director",
        },
    )
    builder.add_edge("catalog", END)
    builder.add_edge("circulation", END)
    builder.add_edge("membership", END)
    builder.add_edge("reference", END)
    builder.add_edge("director", END)

    return builder.compile()
