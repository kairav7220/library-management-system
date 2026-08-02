# Library Management System — Multi-Agent Staff Plan

> A LangGraph-powered multi-agent system where each agent is a real library
> professional, performing CRUD on Google Sheets and answering queries via RAG.

---

## 1. The Problem

We have a Flask app with 10 Google Sheets worksheets managing a library.
Everything is manual — a user clicks through forms to add books, issue them,
register members, etc. We want to replace that with **conversational agents**
that understand intent and do the work.

---

## 2. The Solution — 5 AI Agents

Each agent is modeled after a real library staff position. They share the same
Google Sheets backend but each controls only their domain.

| # | Agent | Real Role | Sheets They Control | CRUD Scope |
|---|-------|-----------|---------------------|------------|
| 1 | **Catalog Librarian** | Cataloger / Collection Dev | `Book Table`, `Book Category`, `Book Genre` | Add, edit, delete books, categories, genres |
| 2 | **Circulation Librarian** | Circulation Desk Staff | `Book Issue`, `Book Sell` | Issue books, process returns, handle book sales |
| 3 | **Membership Services** | Membership / Front Desk | `Member Table`, `Subscription Table`, `Payment Table` | Register members, manage subscriptions, process payments |
| 4 | **Reference Librarian** | Reference / Research | All book data (read-only via RAG) | Search, recommend, answer collection questions |
| 5 | **Library Director** | Chief Librarian / Director | All sheets (read-only, for oversight) | Routes tasks, delegates to specialists, generates reports |

---

## 3. Architecture Overview

```
                        ┌─────────────────────┐
                        │      User (Chat)     │
                        └─────────┬───────────┘
                                  │
                        ┌─────────▼───────────┐
                        │   Library Director   │  ← Orchestrator
                        │   (analyzes intent)  │
                        └─────────┬───────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
    ┌─────────▼────────┐ ┌───────▼───────┐ ┌────────▼────────┐
    │ Catalog          │ │ Circulation   │ │ Membership      │
    │ Librarian        │ │ Librarian     │ │ Services        │
    │                  │ │               │ │                 │
    │ • Book Table     │ │ • Book Issue  │ │ • Member Table  │
    │ • Book Category  │ │ • Book Sell   │ │ • Subscription  │
    │ • Book Genre     │ │               │ │ • Payment Table │
    └──────────────────┘ └───────────────┘ └─────────────────┘

                        ┌─────────────────────┐
                        │  Reference Librarian │
                        │  (RAG — read-only)   │
                        │  ChromaDB + Books    │
                        └─────────────────────┘
```

### How It Works

1. User types a message in the chat widget
2. **Library Director** receives it, analyzes intent
3. Director routes to the correct specialist agent (or handles it themselves)
4. Specialist agent calls the appropriate tool (CRUD or RAG)
5. **Peer-to-peer:** agents may consult each other mid-task (e.g., Circulation
   asks Membership to validate a member) before responding
6. Response flows back to the user

> **Confirmed:** Agents may talk to each other (peer-to-peer), not just
> Director-delegated routing. The Director handles initial intent + oversight;
> specialists can coordinate directly afterwards.

---

## 4. Agent Details

### 4.1 Catalog Librarian

**Personality:** Meticulous, organized, obsessed with proper classification.
Thinks in taxonomies and metadata.

**Can do:**
- Add a new book to the Book Table
- Edit book details (name, author, price, edition, publication)
- Soft-delete a book
- Add/edit/delete book categories
- Add/edit/delete book genres
- Search books by name, author, or category

**Cannot do:** Issue books, manage members, handle payments.

**Tools bound:** `get_all_records`, `add_record`, `update_record`,
`soft_delete`, `search_records` — scoped to Book/Category/Genre sheets.

### 4.2 Circulation Librarian

**Personality:** Efficient, fast-paced, keeps things moving. Knows every
transaction that happened today.

**Can do:**
- Issue a book to a member (creates Book Issue record)
- Process a book return (updates received_by and returned_date)
- Record a book sale (creates Book Sell record)
- Check who has what book out
- View outstanding issues

**Cannot do:** Register members, manage subscriptions, edit book catalog.

**Tools bound:** `get_all_records`, `add_record`, `update_record`,
`search_records` — scoped to Book Issue / Book Sell sheets. Also read-only
access to Book Table and Member Table for validation lookups.

### 4.3 Membership Services

**Personality:** Welcoming, patient, detail-oriented. Handles the human side.

**Can do:**
- Register a new member (creates User + Member records)
- Edit member details
- Soft-delete a member
- Create/edit/delete subscriptions
- Record payments
- Look up member history

**Cannot do:** Issue books, modify book catalog.

**Tools bound:** `get_all_records`, `add_record`, `update_record`,
`soft_delete`, `search_records` — scoped to Member/Subscription/Payment sheets.
Also read-only access to User Table for user lookups.

### 4.4 Reference Librarian

**Personality:** Knowledgeable, passionate about books, loves helping people
find exactly what they need.

**Can do:**
- Answer questions about the book collection using RAG
- Recommend books based on genre, topic, or mood
- Search books semantically (not just keyword match)
- Provide author information, publication details
- Answer "what books do we have about X?"

**Cannot do:** Any write operations. Read-only, RAG-powered.

**Tools bound:** `search_books` (ChromaDB vector search). Read-only access
to all sheets for supplementary data.

### 4.5 Library Director

**Personality:** Decisive, strategic, sees the big picture. Delegates to
specialists and only handles things that need oversight.

**Can do:**
- Route requests to the correct specialist agent
- Handle requests that span multiple agents
- Generate reports (total members, popular books, revenue, etc.)
- Answer meta questions ("how many books do we have?")
- Handle ambiguous requests by asking clarifying questions

**Cannot do:** Directly modify data (always delegates writes to specialists).

**Tools bound:** `get_all_records` (read-only, all sheets) for reports and
oversight. Routing logic for delegation.

---

## 5. Tool Layer

All tools are LangChain `@tool` decorated functions. They wrap the existing
gspread logic from `flask_app.py`.

### 5.1 CRUD Tools — `tools/*.py` (per-domain modules)

The original design planned a single generic `gsheets_tools.py`; in practice each
domain got its own module (`book.py`, `book_cat.py`, `book_genre.py`, `users.py`,
`members.py`, `employees.py`, `subscriptions.py`, `payment.py`, `book_issue.py`,
`book_sell.py`), each exposing LangChain `@tool` CRUD functions:

```python
@tool
def get_all_records(sheet_name: str) -> list[dict]:
    """Read all non-deleted records from a sheet."""

@tool
def get_record_by_id(sheet_name: str, record_id: str) -> dict:
    """Find a single record by its ID (e.g., BOOK_1, MEM_3)."""

@tool
def add_record(sheet_name: str, data: dict) -> str:
    """Add a new record to a sheet. Returns confirmation."""

@tool
def update_record(sheet_name: str, record_id: str, data: dict) -> str:
    """Update an existing record by ID."""

@tool
def soft_delete(sheet_name: str, record_id: str) -> str:
    """Soft-delete a record (sets status to '1')."""

@tool
def search_records(sheet_name: str, query: str, fields: list[str]) -> list[dict]:
    """Search for records matching a text query in specified fields."""
```

### 5.2 RAG Tool — `tools/rag_tools.py`

```python
@tool
def search_books_rag(query: str) -> str:
    """Search the book collection semantically. Returns matching books
    with name, author, category, genre, and publication."""
```

### 5.3 Shared Helpers

- `tools/__init__.py` — Exports all tools
- `tools/llm.py` — Mistral AI client initialization
- `tools/gsheets_client.py` — Shared gspread connection (reuse existing
  credentials logic from `flask_app.py`)

---

## 6. RAG Pipeline

### 6.1 Components

| Component | Choice | Why |
|-----------|--------|-----|
| Vector Store | **ChromaDB** | Local, zero-config, file-based, no server needed |
| Embeddings | **sentence-transformers** (`all-MiniLM-L6-v2`) | Fast, small, free, runs locally |
| Documents | Book metadata (name, author, category, genre, publication) | What users will query about |

### 6.2 Data Flow

```
Google Sheets (Book Table)
        │
        ▼
  rag/loader.py              ← Extract rows, format as documents
        │
        ▼
  rag/embedder.py            ← Embed with sentence-transformers
        │
        ▼
  Postgres + pgvector (Neon) ← book_embeddings table (or local ChromaDB fallback)
        │
        ▼
  Reference Librarian        ← Queries via search_books_rag
```

> **Confirmed:** RAG scope = **books only** (user decision). Library policies
> are NOT indexed. Only the book catalog is semantically searchable.

### 6.3 Document Format

Each book becomes one document:

```python
Document(
    page_content="Dune by Frank Herbert, Science Fiction, 1965, Chilton Books",
    metadata={
        "doc_type": "book",
        "book_id": "BOOK_1",
        "name": "Dune",
        "author": "Frank Herbert",
        "category": "Science Fiction",
        "genre": "Sci-Fi",
        "publication": "Chilton Books"
    }
)
```

### 6.4 Indexing

- Initial index: On app startup (books only)
- Re-index: Automatic — `add_book`, `update_book`, `delete_book` rebuild the
  index after every write (see `tools/book.py`)
- Stored in: Neon Postgres `book_embeddings` table (pgvector, cosine distance
  via `embedding <=>`) when `DATABASE_URL` is set; local `./data/chroma_db/`
  directory as fallback.

---

## 7. Graph Orchestration (LangGraph)

### 7.1 State

```python
class AgentState(TypedDict):
    messages: list          # Conversation history
    next: str               # Which agent to route to
    context: dict           # Shared context (member data, book data, etc.)
    scratchpad: str         # Intermediate results for multi-step flows
```

### 7.2 Graph Structure

```
                    ┌──────────┐
                    │ __start__│
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │ Director │  ← Node 1: Analyze intent, decide route
                    └────┬─────┘
                         │
              ┌──────────┼──────────┐──────────┐
              │          │          │          │
         ┌────▼───┐ ┌────▼───┐ ┌───▼────┐ ┌──▼──────┐
         │Catalog │ │Circul. │ │Member. │ │Reference│
         │Agent   │ │Agent   │ │Agent   │ │Agent    │
         └────┬───┘ └────┬───┘ └───┬────┘ └──┬──────┘
              │          │          │          │
              └──────────┼──────────┘──────────┘
                         │
                    ┌────▼─────┐
                    │  __end__ │
                    └──────────┘
```

### 7.3 Routing Logic (Director)

The Director uses the LLM to classify intent:

| Intent Pattern | Routes To |
|----------------|-----------|
| "add/edit/delete book", "manage categories" | Catalog Librarian |
| "issue book", "return book", "book sale" | Circulation Librarian |
| "register member", "subscription", "payment" | Membership Services |
| "find books about...", "recommend...", "what do we have" | Reference Librarian |
| "show stats", "report", "overview", ambiguous | Director (handles directly) |

### 7.4 Peer-to-Peer Messaging

Agents can consult each other directly. Two mechanisms:

1. **Agent-to-agent tool:** each specialist exposes a
   `consult_<agent_name>(question)` tool that other agents can call to ask a
   question mid-task (e.g., Circulation → Membership: "Is MEM_2 active?").
2. **Graph edges:** for known coordination patterns, connect agents in the
   graph (e.g., Circulation → Membership validation edge before issuing).

> **Confirmed:** peer-to-peer allowed. Start with the `consult_*` tool
> mechanism (simpler, more flexible), add explicit graph edges only for
> high-frequency workflows.

### 7.5 Persistent Memory

Conversation history and agent knowledge persist across sessions.

```
chat_history (SQLite table)
  ├── session_id
  ├── user_message
  ├── agent_response
  ├── agent_name          ← which agent handled it
  ├── tool_calls          ← what tools were invoked
  └── created_at

Memory is loaded into AgentState["messages"] at session start
and appended after every turn.
```

> **Confirmed:** persistent memory via SQLite. Store per-session history +
> which agent handled what, so agents can recall prior conversations.

### 7.6 Conditional Edges

```python
def route_request(state):
    """Director decides which agent handles this request."""
    last_message = state["messages"][-1]
    # LLM classifies intent → returns agent name
    classification = llm.invoke(classify_prompt.format(message=last_message))
    return classification.next_agent
```

---

## 8. Subgraphs (Multi-Step Workflows)

Some operations need multiple agents working in sequence. These are modeled
as LangGraph subgraphs.

### 8.1 Member Onboarding

```
User: "Register a new member named John, email john@example.com"

Director → Membership Agent
  │
  ├── Step 1: Create User record (User Table)
  ├── Step 2: Create Member record (Member Table, linked to User)
  └── Step 3: Create Subscription (Subscription Table)

  → Returns: "John registered successfully. User ID: USER_5, Member ID: MEM_3"
```

### 8.2 Book Acquisition

```
User: "Add 'Neuromancer' by William Gibson to the collection under Sci-Fi"

Director → Catalog Agent
  │
  ├── Step 1: Check if category "Sci-Fi" exists
  ├── Step 2: Add book to Book Table
  ├── Step 3: Update Book Genre with new book name
  └── Step 4: Re-index RAG (embed the new book)

  → Returns: "Added 'Neuromancer' by William Gibson to Sci-Fi collection."
```

### 8.3 Book Issue Flow

```
User: "Issue book BOOK_1 to member MEM_2"

Director → Circulation Agent
  │
  ├── Step 1: Validate member exists and is active
  │     └── (peer-to-peer) consult Membership Agent → confirms MEM_2 active
  ├── Step 2: Validate book exists and is available
  ├── Step 3: Create Book Issue record
  └── Step 4: Confirm with details

  → Returns: "Book 'Dune' issued to member 'Alice'. Due in 14 days."
```

### 8.4 Deletion Confirmation Flow

```
User: "Delete book BOOK_1"

Director → Catalog Agent
  │
  ├── Step 1: Prepare deletion (book "Dune" marked for soft-delete)
  ├── Step 2: ASK USER for confirmation   ← required for all deletes
  │     "Are you sure you want to delete 'Dune'? This hides it from the catalog."
  ├── Step 3: (after user says yes) soft_delete → status = '1'
  └── Step 4: Re-index RAG

  → Returns: "Deleted 'Dune' from the catalog."
```

> **Confirmed:** deletes always require explicit user confirmation before
> executing. Adds/edits execute automatically.

---

## 9. Chat UI

### 9.1 Design (built)

- **Floating launcher** (blue `#5B8DEF` pill, bottom-right of every page) →
  opens a 376px panel with header, message thread, and composer
- Palette matches the app: blue `#5B8DEF` primary, page `#F5F7FA`, white
  panels, success green `#3A9D6A` on mint `#E8F8F0`, muted slate `#8896A7`
- Agent responses rendered as **markdown** client-side (HTML is escaped
  first): `**bold**`, *italic*, `inline code`, fenced code, headings, lists,
  blockquotes, links, and pipe **tables** → real `<table>` in a horizontally
  scrollable `.table-wrap` (headers never wrap vertically)
- **Typing indicator** while the agent works
- **Copy button** on bot messages (appears on hover; shows a check on copy)
- **Timestamps** under every message ("3:45 PM")
- **Unread badge** on the launcher when the widget is closed and a response
  arrives (clears on open)
- **New chat** button (header): clears the thread, generates a fresh
  session id
- **History button** (header): lists past sessions via `GET /chat/sessions`,
  each auto-titled from its first user message (truncated to ~30 chars);
  click a session to resume it
- Session id persisted in `localStorage` (`lib_chat_session`), so a reload
  keeps the same conversation

### 9.2 Files

```
templates/chat_widget.html   ← launcher + panel + session-list overlay (included in 11 pages)
static/styles/chat.css       ← widget styles + markdown/table styling
static/js/chat.js            ← open/close, markdown renderer, /chat fetch,
                               history load, copy, badge, timestamps, session list
```

### 9.3 Flask Routes

```python
@app.route('/chat', methods=['POST'])            # run through LangGraph → {response, agent}
@app.route('/chat/history', methods=['GET'])     # ?session_id= → {turns: [...]}
@app.route('/chat/sessions', methods=['GET'])    # → {sessions: [{session_id, title, created_at, last_active}]}
```

---

## 10. File Structure

```
D:\Projects\testing\
│
├── flask_app.py                    # Existing — add /chat route
├── agents.py                       # Will contain graph definition + orchestration
├── PLAN.md                         # This file
│
├── tools/                          # Phase 1: Tool Layer
│   ├── __init__.py
│   ├── gsheets_client.py           # Shared gspread connection (cached + retry)
│   ├── book.py                     # Book Table CRUD tools (auto-reindex on write)
│   ├── book_cat.py                 # Book Category CRUD tools
│   ├── book_genre.py               # Book Genre CRUD tools
│   ├── users.py / members.py / employees.py
│   ├── subscriptions.py / payment.py / book_issue.py / book_sell.py
│   ├── rag_tools.py                # RAG search + reindex tools (books only)
│   ├── consult.py                  # Peer-to-peer consult tools
│   └── llm.py                      # Mistral AI client + LangSmith setup
│
├── rag/                            # Phase 2: RAG Pipeline
│   ├── __init__.py
│   ├── config.py                   # ChromaDB path, embedding model
│   ├── loader.py                   # Sheet → Documents (books only)
│   └── embedder.py                 # Embed + index (pgvector on Neon / ChromaDB fallback)
│
├── agents/                         # Phase 3: Agent Definitions
│   ├── __init__.py
│   ├── catalog_agent.py
│   ├── circulation_agent.py
│   ├── membership_agent.py
│   ├── reference_agent.py
│   └── director_agent.py
│
├── graph/                          # Phase 4: Graph Orchestration
│   ├── __init__.py
│   ├── state.py                    # AgentState definition
│   ├── memory.py                   # Chat memory — Neon Postgres (DATABASE_URL) or SQLite fallback
│   ├── orchestrator.py             # Graph construction + routing
│   └── subgraphs.py                # Multi-step workflows
│
├── data/                           # Persistent storage
│   ├── chat_history.db             # SQLite (conversation memory)
│   └── chroma_db/                  # RAG vector store
│
├── static/styles/
│   ├── style.css                   # Existing
│   └── chat.css                    # Phase 6: Chat styles
│
├── templates/
│   ├── (existing 29 templates)
│   └── chat_widget.html            # Phase 6: Chat widget
│
├── requirements.txt                # Add new dependencies
└── vercel.json                     # Existing
```

---

## 11. Dependencies

### New (add to requirements.txt)

```
langgraph
langchain-core
langchain-mistralai
langsmith
chromadb
sentence-transformers
psycopg[binary]                     # Postgres driver for chat memory
```

### Existing (keep)

```
flask
gspread
google-auth-oauthlib
google-auth-httplib2
google-api-python-client
python-dotenv
```

### Env Vars (new)

```
MISTRAL_API_KEY=...
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=library management system
DATABASE_URL=...                    # Neon Postgres (chat memory); optional — SQLite fallback
```

---

## 12. Build Phases

### Phase 0: Setup
- [ ] Add dependencies to `requirements.txt`
- [ ] Create `.env` with all keys (Mistral, LangSmith, Google)
- [ ] Enable LangSmith tracing (`LANGSMITH_TRACING=true`)
- [ ] Verify existing Flask app still runs

### Phase 1: Tool Layer
- [ ] `tools/gsheets_client.py` — Shared connection (cached + rate-limit retry)
- [ ] `tools/llm.py` — Mistral client + full tool registry
- [ ] `tools/rag_tools.py` — RAG search + reindex tools (books only)
- [ ] `tools/consult.py` — Peer-to-peer consult tools
- [ ] Test each tool independently

### Phase 2: RAG Pipeline
- [ ] `rag/config.py` — Config
- [ ] `rag/loader.py` — Sheet → Documents (books only)
- [ ] `rag/embedder.py` — pgvector (Neon) / ChromaDB embedding + indexing
- [ ] Index books
- [ ] Test: search books, verify results

### Phase 3: Agent Definitions
- [ ] Define each agent with system prompt + tools (incl. app-internal docs)
- [ ] Test each agent individually with mock inputs

### Phase 4: Graph Orchestration
- [ ] `graph/state.py` — State definition
- [ ] `graph/memory.py` — SQLite persistent memory
- [ ] `graph/orchestrator.py` — Build graph with Director routing
- [ ] `graph/subgraphs.py` — Multi-step workflows (incl. delete-confirm)
- [ ] Test: end-to-end routing through Director

### Phase 5: Integrate with Flask
- [ ] Add `/chat` route to `flask_app.py`
- [ ] Connect graph + memory to the route
- [ ] Test: send message via curl, get response
- [ ] Test: delete flow asks confirmation, then executes

### Phase 6: Chat UI
- [ ] `templates/chat_widget.html` — Floating icon + modal
- [ ] `static/styles/chat.css` — Styles
- [ ] Include widget in base template / all pages
- [ ] Test: full user interaction flow

---

## 13. Decisions (Confirmed by Owner)

| # | Question | Decision | Implication |
|---|----------|----------|-------------|
| 1 | **Agent confirmation before CRUD?** | **Confirm before deletes only.** Adds/edits auto-execute. | Deletes always ask user to confirm first; other writes run immediately. |
| 2 | **Agent communication?** | **Peer-to-peer.** Agents can talk to each other, not just Director-delegated. | Circulation Agent can ask Membership Agent to validate a member. Add agent-to-agent tool/messaging. |
| 3 | **Conversation memory?** | **Persistent.** Agents remember across sessions. | Need a memory store (e.g., SQLite or the Sheets themselves) for conversation history + agent knowledge. |
| 4 | **RAG scope?** | **Books only.** Not policies/FAQs. | Only the book catalog is indexed and semantically searched (`search_books_rag`). |
| 5 | **System meta-knowledge?** | **Yes.** Agents know how the app works. | Agents get docs on the sheet schemas, workflows, and how to use tools. |
| 6 | **LangSmith?** | **Yes, from start.** | Set up tracing + observability in Phase 1. Add API key. |
| 7 | **Chat UI ownership?** | **Owner-provided design.** | Owner supplied the blue-themed widget; agent integrated it, wired the backend, and added markdown/UX features. |
| 8 | **RAG reindexing?** | **Automatic, deterministic.** | `add_book`/`update_book`/`delete_book` rebuild the index; no LLM-trusted reindex step. |

---

## 14. Post-Build Loose Ends

| # | Item | Status |
|---|------|--------|
| 1 | Auto-reindex RAG after book writes | Done — `tools/book.py` rebuilds index on add/update/delete; tested |
| 2 | Register missing consult tools (`consult_catalog`, `consult_circulation`) | Done — in `tools/llm.py` + per-agent tool lists; verified loading |
| 3 | Update PLAN.md (this section) | Done |
| 4 | Vercel persistence for memory + RAG | **Done** — `graph/memory.py` uses Neon Postgres (`DATABASE_URL` in `.env`) when present, falls back to SQLite locally. `rag/embedder.py` stores embeddings in a `book_embeddings` table (pgvector, Neon) when `DATABASE_URL` is set, falls back to local ChromaDB. Both verified end-to-end via `/chat`. |
| 5 | RAG index persistence on serverless | **Done** — embeddings live in Neon Postgres `book_embeddings` table via pgvector extension + `pgvector` Python package. Auto-reindex verified (add/delete → search reflects immediately). |
| 6 | Chat widget redesign + markdown rendering | **Done** — owner-provided blue `#5B8DEF` design integrated (launcher + panel). Responses rendered as markdown client-side (bold, tables, lists, code, headings); HTML escaped before transform. Tables render in a scrollable wrapper instead of compressing vertically. |
| 7 | Chat widget UX features | **Done** — copy button on bot messages, timestamps, unread badge on launcher, reset/"new chat" button. Suggestion chips removed at owner's request. |
| 8 | Chat history / resume sessions | **Done** — `GET /chat/sessions` lists sessions auto-titled from their first user message (truncated ~30 chars), newest first; history button in the widget opens the list; clicking a session loads its turns and continues it. |

---

## 14. How We Split the Work

> TBD — decide together before starting Phase 1.

Possible splits:
- **You build tools, I build agents + graph**
- **I build everything, you review each phase**
- **Parallel: you do RAG, I do tools + agents**
- **Phase-by-phase together, alternating who leads**

---

*This plan is a living document. Update as we make decisions and build.*
