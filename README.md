<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=200&section=header&text=Library%20Management%20System&fontSize=50&fontAlignY=35&desc=Lumina%20Concierge%20%E2%80%94%20Multi-Agent%20AI%20Library%20Assistant&descAlignY=55" />
</p>

<p align="center">
  <a href="https://library-management-system-mocha-delta.vercel.app/" target="_blank">
    <img src="https://img.shields.io/badge/Live_Demo-Vercel-000000?logo=vercel&logoColor=white" alt="Live Demo"/>
  </a>
</p>

<p align="center">
  <a href="#features">Features</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#agents">Agents</a> ·
  <a href="#quick-start">Quick Start</a> ·
  <a href="#configuration">Configuration</a> ·
  <a href="#api">API</a> ·
  <a href="#project-structure">Structure</a> ·
  <a href="#comparison">Comparison</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11-blue?logo=python&logoColor=white" alt="Python 3.11"/>
  <img src="https://img.shields.io/badge/Flask-Web-000000?logo=flask&logoColor=white" alt="Flask"/>
  <img src="https://img.shields.io/badge/LangGraph-Agentic-blueviolet" alt="LangGraph"/>
  <img src="https://img.shields.io/badge/Mistral-LLM-blue" alt="Mistral"/>
  <img src="https://img.shields.io/badge/RAG-pgvector-4169E1?logo=postgresql&logoColor=white" alt="pgvector RAG"/>
  <img src="https://img.shields.io/badge/SSE-Streaming-green" alt="SSE Streaming"/>
  <img src="https://img.shields.io/badge/Google%20Sheets-Data-orange?logo=google" alt="Google Sheets"/>
  <img src="https://img.shields.io/badge/Vercel-Deploy-000000?logo=vercel&logoColor=white" alt="Vercel"/>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License"/>
</p>

---

A full-featured library management system with a Material 3 chat widget powered by five LangGraph librarian agents. Manage books, members, employees, subscriptions, payments, and issues — or just ask **Lumina Concierge** in plain language.

## Features

- **🧑‍💼 Multi-Agent AI Concierge** — Five specialized LangGraph agents (Catalog, Circulation, Membership, Reference, Director) routed by an intent classifier
- **⚡ Token-Level Streaming** — Agent replies stream live via Server-Sent Events (SSE) with a typing indicator
- **📚 Full CRUD Management** — Books, categories, genres, members, employees, subscriptions, payments, book sales, and book issues
- **🗂️ Chat History & Resume** — Sessions persist in Postgres/SQLite; browse and resume past conversations, delete stale sessions
- **🔎 RAG Book Search** — Semantic book discovery via Mistral embeddings + pgvector on Neon Postgres
- **🧾 Google Sheets Backend** — All CRUD data lives in a live Google Sheet (service account auth)
- **📱 Material 3 UI** — Responsive chat widget with Hanken Grotesk typography, session overlay, markdown tables
- **☁️ Serverless-Ready** — Deploys to Vercel with a single Flask app entry point

## Architecture

```mermaid
flowchart LR
  User["🙋 User"] --> Widget["💬 Chat Widget<br/>(Material 3)"]
  Widget -->|"POST /chat/stream"| SSE["SSE Stream<br/>(Flask)"]
  SSE --> Classifier["🧭 Intent Classifier<br/>(LCEL)"]
  Classifier --> Director["🧑‍💼 Library Director<br/>(reports, overviews)"]
  Classifier --> Catalog["📖 Catalog Librarian<br/>(books, categories, genres)"]
  Classifier --> Circulation["🔄 Circulation Librarian<br/>(issue, return, sell)"]
  Classifier --> Membership["👥 Membership Services<br/>(members, subscriptions, payments)"]
  Classifier --> Reference["🔎 Reference Librarian<br/>(read-only, RAG)"]
  Director --> Tools1["🛠️ gsheets_tools"]
  Catalog --> Tools1
  Circulation --> Tools1
  Membership --> Tools1
  Reference --> RAG["🧠 RAG + pgvector"]
  RAG --> Tools2["📖 book_search_tool"]
```

| Layer | Technology |
|---|---|
| **Frontend** | Chat widget (Material 3, CSS), server-rendered admin pages (Jinja2) |
| **API** | Flask — REST CRUD + `POST /chat/stream` SSE |
| **Orchestration** | LangGraph StateGraph — classifier routes to 5 react agents |
| **LLM** | Mistral (`open-mistral-7b` via `langchain-mistralai`) |
| **RAG** | Mistral embeddings + pgvector (`book_embeddings` table) |
| **Persistence** | Google Sheets (CRUD) + Postgres/SQLite (chat sessions) |
| **Deployment** | Vercel (`@vercel/python`, `flask_app.py` entry) |

## Agents

| Agent | Responsibility | Tools |
|---|---|---|
| **🧭 Intent Classifier** | Routes each message to the right specialist | LCEL structured output (Pydantic) |
| **🧑‍💼 Library Director** | Statistics, reports, overviews, greetings, ambiguous requests | GSheets aggregates |
| **📖 Catalog Librarian** | Add/edit/delete books, categories, genres | `book_tools`, `book_cat`, `book_genre` |
| **🔄 Circulation Librarian** | Issue, return, and sell books | `book_issue`, `book_sell` |
| **👥 Membership Services** | Register members/employees, subscriptions, payments | `members`, `employees`, `subscriptions`, `payment` |
| **🔎 Reference Librarian** | Book discovery, recommendations, collection questions (read-only) | RAG + `book_search_tool` |

## Quick Start

```bash
git clone https://github.com/kairav7220/testing.git
cd testing
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your keys (see [Configuration](#configuration)):

```env
MISTRAL_API_KEY="your_mistral_api_key_here"
GOOGLE_SHEET_ID="your_google_sheet_id_here"
GOOGLE_CREDENTIALS='{...service account json...}'
DATABASE_URL="postgresql://user:pass@host:5432/library"
```

Then run:

```bash
flask run            # or: python flask_app.py
```

Open `http://localhost:5000` — the admin CRUD pages load data from Google Sheets, and the **Lumina Concierge** chat widget is embedded for AI assistance.

## Configuration

| Variable | Required | Purpose |
|---|---|---|
| `MISTRAL_API_KEY` | ✅ | Mistral LLM + embeddings |
| `GOOGLE_SHEET_ID` | ✅ | Spreadsheet ID for all CRUD tables |
| `GOOGLE_CREDENTIALS` | ✅* | Service-account JSON (inline) |
| `GOOGLE_SHEETS_CREDS_PATH` | ✅* | Or: path to `credentials.json` file |
| `DATABASE_URL` | ⚠️ | Postgres for RAG + chat sessions (falls back to SQLite) |
| `LANGSMITH_*` | optional | LangSmith tracing (`TRACING`, `ENDPOINT`, `API_KEY`, `PROJECT`) |

\* Use either `GOOGLE_CREDENTIALS` (JSON string) **or** `GOOGLE_SHEETS_CREDS_PATH` (file path).

To build the vector index once RAG is configured:

```bash
python -m rag.embedder    # embeds books into pgvector book_embeddings
```

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat` | Non-streaming agent reply |
| `POST` | `/chat/stream` | SSE streaming agent reply (delta → done events) |
| `GET` | `/chat/history?session_id=` | Turn history for a session |
| `GET` | `/chat/sessions` | List saved sessions |
| `DELETE` | `/chat/sessions/<id>` | Delete a session |
| `GET` | `/books`, `/members`, `/employees` … | CRUD list pages (Jinja2) |
| `POST` | `/books/add`, `/members/add`, … | CRUD create |
| `GET` | `/books/edit/<row>`, `/books/delete/<row>`, … | CRUD update/delete |

## Comparison

| Feature | This System | Basic CRUD App | Plain Chatbot |
|---|---|---|---|
| CRUD Management | ✅ 9 entities (books → issues) | ✅ | ❌ |
| AI Assistant | ✅ 5-agent LangGraph | ❌ | ✅ single model |
| Streaming Replies | ✅ SSE token-by-token | ❌ | ❌ |
| Semantic Search | ✅ RAG + pgvector | ❌ | ❌ |
| Chat History / Resume | ✅ Postgres/SQLite sessions | ❌ | ✅ (in-memory only) |
| Multi-Agent Routing | ✅ Intent classifier | ❌ | ❌ |
| Data Layer | ✅ Google Sheets (live) | ✅ DB | — |
| Deployment | ✅ Vercel serverless | ✅ | ✅ |

## Project Structure

```
library-management-system/
├── flask_app.py                # Flask entry — CRUD routes + chat/SSE endpoints
├── vercel.json                 # Vercel serverless config
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── .gitignore                  # Git ignore rules
├── agents/
│   ├── __init__.py
│   ├── director_agent.py       # Library Director (reports, overviews)
│   ├── catalog_agent.py        # Catalog Librarian (books, categories, genres)
│   ├── circulation_agent.py    # Circulation Librarian (issue/return/sell)
│   ├── membership_agent.py     # Membership Services (members, subscriptions)
│   └── reference_agent.py      # Reference Librarian (read-only, RAG)
├── graph/
│   ├── __init__.py
│   ├── orchestrator.py         # StateGraph + intent classifier routing
│   ├── subgraphs.py            # Continuation routing
│   ├── memory.py               # Session persistence (Postgres/SQLite)
│   └── state.py                # Graph state schema
├── rag/
│   ├── __init__.py
│   ├── embedder.py             # pgvector indexing + semantic search
│   ├── loader.py               # Book document loader
│   └── config.py               # Embedding model config
├── tools/
│   ├── __init__.py
│   ├── gsheets_client.py       # Shared Google Sheets client
│   ├── llm.py                  # Mistral LLM factory
│   ├── consult.py              # Agent consultation helpers
│   ├── rag_tools.py            # RAG search tool
│   ├── book.py                 # Book tools
│   ├── book_cat.py             # Book category tools
│   ├── book_genre.py           # Book genre tools
│   ├── book_issue.py           # Book issue tools
│   ├── book_sell.py            # Book sell tools
│   ├── members.py              # Member tools
│   ├── employees.py            # Employee tools
│   ├── subscriptions.py        # Subscription tools
│   ├── payment.py              # Payment tools
│   └── users.py                # User tools
├── templates/                  # Jinja2 admin pages
│   ├── index.html              # Users page
│   ├── books.html              # Books page
│   ├── book_category.html      # Book category page
│   ├── book_genre.html         # Book genre page
│   ├── members.html            # Members page
│   ├── employees.html          # Employees page
│   ├── subscriptions.html      # Subscriptions page
│   ├── payments.html           # Payments page
│   ├── book_sell.html          # Book sell page
│   ├── book_issue.html         # Book issue page
│   ├── chat_widget.html        # Lumina Concierge chat widget
│   ├── add_*.html              # Add forms
│   ├── edit_*.html             # Edit forms
│   ├── form.html               # Shared form template
│   └── return_book_issue.html  # Book return form
├── static/
│   ├── js/
│   │   └── chat.js             # Streaming chat widget logic
│   └── styles/
│       ├── chat.css            # Material 3 chat styling
│       └── style.css           # Admin pages styling
└── (legacy scripts)            # book.py, book_cat.py, members.py, …
```

## License

MIT © [kairav7220](https://github.com/kairav7220)

---

<p align="center">
  Built with <a href="https://flask.palletsprojects.com">Flask</a> ·
  <a href="https://langchain-ai.github.io/langgraph">LangGraph</a> ·
  <a href="https://mistral.ai">Mistral AI</a> ·
  <a href="https://github.com/pgvector/pgvector">pgvector</a> ·
  <a href="https://developers.google.com/sheets">Google Sheets API</a> ·
  <a href="https://vercel.com">Vercel</a>
</p>
