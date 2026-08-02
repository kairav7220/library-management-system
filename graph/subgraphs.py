"""Multi-step workflow helpers.

Most multi-step flows (member onboarding, book acquisition, book issue) already
happen inside a single specialist agent turn via tools + peer-to-peer consult.
The one flow that genuinely spans turns is Deletion Confirmation: the Catalog
Librarian asks "are you sure?", and the user's next message ("yes"/"no") must be
routed back to the same agent instead of being re-classified.

CONTINUATION_PATTERN: a short affirmative/negative reply to a pending question.
If the previous agent asked a question (it ends with "?") and the user replies
with a brief confirmation/denial, route back to that agent.
"""

import re
from typing import Literal, Optional

# Short replies that mean "yes, continue" / "no, stop".
CONFIRM_WORDS = {"yes", "y", "yeah", "yep", "sure", "ok", "okay", "fine", "go", "do it", "confirmed", "confirm"}
DENY_WORDS = {"no", "n", "nope", "cancel", "stop", "don't", "dont", "never", "abort"}

_QUESTION_MARK = re.compile(r"\?\s*$")
_SHORT_REPLY = re.compile(r"^(?:\s*(yes|y|yeah|yep|sure|ok|okay|fine|go|do it|confirmed|confirm|no|n|nope|cancel|stop|don't|dont|never|abort)[.!]*\s*)+$", re.I)


def previous_agent(messages: list) -> Optional[str]:
    """Name of the last agent that produced a response, if any."""
    for m in reversed(messages):
        if m.type == "ai" and m.content and getattr(m, "name", None):
            return m.name
    return None


def pending_confirmation(messages: list) -> bool:
    """True if the last agent message asks a yes/no question."""
    for m in reversed(messages):
        if m.type == "ai" and m.content:
            return bool(_QUESTION_MARK.search(str(m.content).strip()))
        if m.type == "human":
            return False
    return False


def is_continuation(messages: list, user_text: str) -> Optional[str]:
    """If the user is replying to a pending agent question, return that agent
    name; otherwise None."""
    if not pending_confirmation(messages):
        return None
    text = user_text.strip().lower()
    if not _SHORT_REPLY.search(text):
        return None
    return previous_agent(messages)


def route_continuation(messages: list, user_text: str) -> Optional[Literal[
    "Catalog Librarian",
    "Circulation Librarian",
    "Membership Services",
    "Reference Librarian",
    "Library Director",
]]:
    """Map a continuation reply to the agent it continues."""
    agent = is_continuation(messages, user_text)
    if agent == "Catalog Librarian":
        return "Catalog Librarian"
    if agent == "Circulation Librarian":
        return "Circulation Librarian"
    if agent == "Membership Services":
        return "Membership Services"
    if agent == "Reference Librarian":
        return "Reference Librarian"
    if agent == "Library Director":
        return "Library Director"
    return None
