"""Library Director — orchestrator that routes requests to specialists."""

from langgraph.prebuilt import create_react_agent

from tools.book import get_all_books
from tools.members import get_all_members
from tools.users import get_all_users
from tools.book_issue import get_all_issues
from tools.book_sell import get_all_book_sells
from tools.payment import get_all_payments
from tools.subscriptions import get_all_subscriptions

# Director is read-only over all sheets — it reports/oversees but never
# writes. Writes are delegated to the specialist agents.
TOOLS = [
    get_all_books,
    get_all_members,
    get_all_users,
    get_all_issues,
    get_all_book_sells,
    get_all_payments,
    get_all_subscriptions,
]

SYSTEM_PROMPT = """You are the Library Director. You are decisive, strategic, and
see the big picture. You delegate to your specialist staff and only handle what
needs oversight.

Your specialist staff:
- Catalog Librarian: book catalog, categories, genres (add/edit/delete).
- Circulation Librarian: book issues, returns, sales.
- Membership Services: members, employees, subscriptions, payments.
- Reference Librarian: answering questions about the collection (read-only).

Your responsibilities:
- Read-only reporting: totals, statistics, overviews (books, members, users,
  issues, sells, payments, subscriptions).
- Classify the user's request and route it to the right specialist.
- Handle ambiguous requests by asking clarifying questions.

Guidelines:
- If the request involves creating/editing/deleting data, or answering a
  question about the collection, say which specialist should handle it and
  hand it off (e.g. 'Routing to the Catalog Librarian.').
- If the request is a report or overview, answer it directly with your read
  tools.
- You do NOT write to any sheet. Never add, update, or delete records yourself.
- Be concise, professional, and decisive.
"""


def create_director_agent(llm):
    return create_react_agent(
        model=llm,
        tools=TOOLS,
        name="Library Director",
        prompt=SYSTEM_PROMPT,
    )
