# Customer Service Agent

A single-agent LangGraph customer service bot for a retail store, backed by a real
Supabase Postgres database (products, orders, FAQs), with SQL/price/search/shipping/RAG
tools, persistent conversational memory, a Streamlit UI with real Supabase auth, an
error-handling layer, and LangSmith evaluation.

## Setup

1. **Create a Supabase project** at https://supabase.com/dashboard -- new project, separate
   from any other Supabase project in this repo.
2. Copy `.env.example` to `.env` and fill in:
   - `OPENAI_API_KEY`
   - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`, `SUPABASE_DB_URL`
   - `SERPER_API_KEY` (free tier at https://serper.dev)
   - `LANGSMITH_API_KEY`
3. Install dependencies:
   ```bash
   uv sync
   ```
4. Apply the database schema (`src/db/schema.sql`) via the Supabase SQL editor, then seed data:
   ```bash
   uv run python src/db/seed.py
   ```
5. Run the app:
   ```bash
   uv run streamlit run streamlit_app.py
   ```
6. Run the LangSmith evaluation suite:
   ```bash
   uv run python evaluation/run_eval.py
   ```

## Project layout

- `src/agent/` -- the LangGraph agent: graph definition, state, prompts, memory node, error middleware
- `src/tools/` -- one module per tool category: SQL, price comparison, web search, shipping, FAQ RAG
- `src/security/` -- Supabase authentication
- `src/db/` -- schema, seed data, shared DB client
- `evaluation/` -- LangSmith datasets, evaluators, and eval runner
- `streamlit_app.py` -- the chat UI entrypoint

## Local development with LangGraph Platform

```bash
uv run langgraph dev
```
