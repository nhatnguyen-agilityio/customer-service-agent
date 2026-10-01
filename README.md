# Customer Service Agent

A single-agent LangGraph customer service bot for a retail store. It answers
product, order, and policy questions using real tools backed by Supabase
(database + auth), with conversational memory, structured error handling,
and a LangSmith evaluation suite.

## Features

- **Product information** -- look up product details, stock, and price from
  the real catalog; never assumes something is in stock.
- **Price comparison** -- compares a product's price against real current
  market prices from other retailers (Google Serper shopping search), not
  simulated data.
- **Order management** -- order status and delivery estimates, full order
  history, and modification/cancellation requests (explained against the
  real 1-hour policy, with a clear "what I can/can't do" answer).
- **Customer support** -- returns and policy questions (FAQ retrieval/RAG),
  empathetic complaint handling, and product recommendations grounded in the
  real catalog.
- **Related-item suggestions** -- if a requested product doesn't exist, the
  agent checks for related products (same category or a broader keyword) and
  suggests real alternatives instead of a dead-end "not available" answer --
  unless nothing related exists either, in which case it says so plainly.
- **Conversational memory** -- a Postgres-backed checkpointer persists each
  customer's conversation across sessions, with automatic trimming once a
  conversation passes a token threshold.
- **Scoped, on-topic responses** -- declines unrelated/off-topic questions
  (weather, general knowledge, etc.) without using any tool.
- **Per-customer authorization** -- a customer can only ever see their own
  orders, enforced in code (not just prompt instructions).
- **Comprehensive error handling** -- API timeouts, rate limiting,
  authentication issues, database connection errors, invalid input, and
  no-results scenarios are all caught and turned into plain-language
  messages, never a raw stack trace.
- **Real authentication** -- Supabase Auth-backed sign-up/login, not a mock.

## Tech Stack

| Layer | Technology |
|---|---|
| Agent framework | LangGraph (`StateGraph`, `ToolNode`, `PostgresSaver`) |
| LLM orchestration | LangChain (`init_chat_model`, tool calling, structured output) |
| Model | OpenAI `gpt-4o-mini` (agent), `gpt-5.4-mini` (LangSmith judges) |
| Database | Supabase Postgres (`products`, `customers`, `orders`, `order_items`, `documents`) |
| Auth | Supabase Auth |
| Data access | Supabase's auto-generated REST API (PostgREST) for business data; direct Postgres (via a read-only role) for the agent's SQL tool and the checkpointer |
| Vector search / RAG | pgvector + `SupabaseVectorStore`, OpenAI `text-embedding-3-small` |
| Web/price search | Google Serper API |
| UI | Streamlit |
| Evaluation & tracing | LangSmith |
| Package management | [`uv`](https://docs.astral.sh/uv/) |

## Project Structure

```
customer-service-agent/
├── streamlit_app.py          # Chat UI: auth, message rendering, graph invocation
├── src/
│   ├── agent/
│   │   ├── graph.py           # Builds and compiles the LangGraph StateGraph
│   │   ├── state.py           # State schema (messages + add_messages reducer)
│   │   ├── memory.py          # manage_memory node -- trims old messages
│   │   ├── prompts.py         # SYSTEM_PROMPT -- the agent's full behavior spec
│   │   └── errors.py          # handle_tool_errors -- ToolNode error wrapping
│   ├── tools/
│   │   ├── sql_tools.py       # SQL toolkit (read-only DB role)
│   │   ├── price_tools.py     # price_comparison_tool (real market data)
│   │   ├── shipping_tools.py  # shipping_tracker_tool (+ ownership check)
│   │   ├── search_tools.py    # web_search_tool (Google Serper)
│   │   └── rag_tools.py       # faq_lookup_tool (vector search over FAQs)
│   ├── security/
│   │   └── auth.py            # sign_up / login / token verification
│   └── db/
│       ├── schema.sql         # Full DB schema -- run in Supabase SQL Editor
│       └── seed.py            # Seeds products, customers, orders, FAQs
├── evaluation/
│   ├── datasets.py            # LangSmith datasets for all 4 eval categories
│   ├── evaluators.py          # Scoring functions (LLM judges + plain checks)
│   └── run_eval.py            # Runs all 4 categories, prints pass rates
├── scripts/
│   ├── performance_report.py  # Latency/token/cost per category
│   └── prune_checkpoints.py   # Deletes old checkpoint history (dry-run by default)
├── .env.example
└── pyproject.toml
```

## Setup Instructions

### Prerequisites

- Python 3.11-3.13 and `uv`
- A Supabase project
- API keys: OpenAI, Serper, LangSmith

### 1. Supabase project setup

1. Create a new Supabase project.
2. Open **SQL Editor** and run `src/db/schema.sql` in full. This creates:
   - Retail tables: `products`, `customers`, `orders`, `order_items`
   - The `documents` table + `match_documents` RPC used for FAQ retrieval
     (RAG), enabling the `vector` extension along the way
   - A read-only `agent_readonly` Postgres role, so the SQL toolkit tool can
     only ever `SELECT`, never modify data
   - **Before running**, edit the `create role agent_readonly ... password
     '<set a real password>'` line with a real password -- you'll need it for
     `SUPABASE_READONLY_DB_URL` below.
3. In **Project Settings -> API**, copy the Project URL, anon key, and
   service_role key.
4. In **Project Settings -> Database -> Connection string -> URI**, copy the
   connection string twice: once as-is for `SUPABASE_DB_URL`, and once with
   the username/password swapped to `agent_readonly` for
   `SUPABASE_READONLY_DB_URL`.
5. In **Authentication** settings, disable "Confirm email" under Auth
   providers if you want sign-up to work immediately during local testing
   (otherwise a new account can't log in until the confirmation email is
   clicked).

### 2. Environment variables

Copy `.env.example` to `.env` and fill in:

| Variable | Used for |
|---|---|
| `OPENAI_API_KEY` | the agent's model + the LangSmith judge models |
| `SUPABASE_URL` / `SUPABASE_ANON_KEY` / `SUPABASE_SERVICE_KEY` | Supabase's generated REST API + Auth (seeding, tools, sign-up/login) |
| `SUPABASE_DB_URL` | direct Postgres connection for LangGraph's checkpointer (conversation memory) |
| `SUPABASE_READONLY_DB_URL` | the `agent_readonly` role -- used only by the SQL toolkit tool |
| `SERPER_API_KEY` | web search + price comparison tools (Google Serper) |
| `LANGSMITH_TRACING` / `LANGSMITH_API_KEY` / `LANGSMITH_PROJECT` / `LANGSMITH_ENDPOINT` | tracing + the eval suite |
| `CHECKPOINT_RETENTION_INTERVAL` | optional, defaults to `3 days` -- see `scripts/prune_checkpoints.py` |

### 3. Install dependencies

```bash
uv sync
```

### 4. Seed the database

```bash
uv run python -m src.db.seed
```

Populates sample products, customers, and orders, and embeds the FAQ
documents for RAG.

## Running the Application

### The chat app

```bash
uv run streamlit run streamlit_app.py
```

Sign up or log in, then chat with the agent.

### The LangSmith eval suite

```bash
uv run python -m evaluation.run_eval
```

Runs all 4 categories -- response accuracy, tool usage efficiency,
conversation flow, and error handling -- against LangSmith, then prints pass
rates for each. Requires `LANGSMITH_API_KEY`.

### Other on-demand scripts

```bash
# Latency/token/cost per category, pulled from your most recent LangSmith experiments
uv run python -m scripts.performance_report

# Delete checkpoint history older than CHECKPOINT_RETENTION_INTERVAL
# (dry-run by default -- add --apply to actually delete)
uv run python -m scripts.prune_checkpoints [--apply]
```

## Architecture

The agent is a single `StateGraph` with a tool-calling loop:

```
START -> manage_memory -> agent --(tool calls?)--> tools -> agent -> ...
                             |
                             +--(no tool calls)--> END
```

- **`manage_memory`** runs first on every turn. Once a conversation passes a
  token threshold, it trims the oldest messages -- via explicit
  `RemoveMessage` objects, since the `messages` channel's reducer
  (`add_messages`) merges by id and does not delete-by-omission.
- **`agent`** (`call_model`) calls the LLM with the full system prompt (plus
  a per-request note identifying the current customer, used for
  authorization) and the conversation so far.
- **`tools`** is a `ToolNode` wrapping 4 real tools plus the SQL toolkit
  (`sql_db_list_tables`, `sql_db_schema`, `sql_db_query`,
  `sql_db_query_checker`). Tool-level failures (timeouts, auth errors, rate
  limits, DB connection errors) are caught by `handle_tool_errors` and turned
  into a plain-language `ToolMessage` instead of propagating as an exception.
- The graph loops `agent -> tools -> agent` until the model responds with no
  further tool calls, then ends the turn.

**Persistence**: a `PostgresSaver` checkpointer, backed by a
`psycopg_pool.ConnectionPool` (not a single raw connection), stores the full
conversation state per customer (`thread_id` = customer email) in Postgres.
The pool recycles idle/aged connections in the background and validates a
connection before handing it out, so a connection going stale from sitting
idle doesn't crash the next request.

**Authorization**: the system prompt instructs the model to only look up the
current customer's own data, and `shipping_tracker_tool` additionally
enforces this in code via `ToolRuntime` -- a real, code-level guarantee, not
just a prompt-level one.

**Resilience**: the agent's main model and both LangSmith judge models use
`.with_retry()` with exponential backoff on transient OpenAI errors (rate
limits, connection errors, server errors), so a momentary API hiccup doesn't
crash a request.

## LangSmith Tracing

Tracing is automatic -- no extra code required. Once `LANGSMITH_TRACING=true`
and `LANGSMITH_API_KEY` are set in `.env`, every `graph.invoke()` call
(from the Streamlit app, the eval suite, or anywhere else) is traced to your
LangSmith project automatically, including every LLM call, tool call, and
their latency/token/cost -- the same way tracing works for any LangChain/
LangGraph app once the env vars are set.

This is distinct from the **eval suite** (`evaluation/`), which runs curated
test datasets against the agent and scores the results:

| Category | What it checks | Evaluator |
|---|---|---|
| Response accuracy | Is the final answer factually correct? | LLM-as-judge |
| Tool usage efficiency | Did the agent call the expected tool(s)? | Deterministic check |
| Conversation flow | Does a multi-turn reply correctly use earlier context? | LLM-as-judge |
| Error handling | Does a failure/edge case produce a graceful message, not a leaked error? | Deterministic check |

`scripts/performance_report.py` reads back the latency/token/cost data
LangSmith already recorded for your most recent experiment in each category
-- it doesn't add any new tracking, just surfaces what's already there.

## License & Author

This project is for educational purposes as part of LangChain & LangGraph training.

Author: Nhat Nguyen
