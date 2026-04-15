# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Mr. Injector** is an interactive educational web application demonstrating LLM security vulnerabilities (prompt injection, jailbreaking, RAG poisoning, agent security, etc.). It's built with Streamlit and supports multiple LLM providers.

## Commands

```bash
# Install dependencies
uv sync

# Run locally (activate venv first)
. .venv/bin/activate
streamlit run mr_injector/frontend/main.py

# Docker build and run
docker build -t mr-injector .
docker run -p 8501:8501 mr-injector

# Docker with optional build args
docker build \
  --build-arg STREAMLIT_PASSWORD=<password> \
  --build-arg AZURE_OPENAI_ENDPOINT=<url> \
  --build-arg AZURE_OPENAI_API_KEY=<key> \
  --build-arg USE_OPEN_AI_EMBEDDINGS=true \
  -t mr-injector .
```

There are no automated tests or linting configured.

## Architecture

### Frontend (`mr_injector/frontend/`)

**Module system** — Each interactive learning exercise is a module in `frontend/modules/`. All modules inherit from `ModuleView` (defined in `modules/main.py`) and are registered in `AppSession.modules` (in `session.py`). The `ModuleNames` enum is the canonical list of all modules.

**Navigation** is hierarchical: Introduction → categories (LLM Security, Agent Security, Prompt Engineering) → individual modules. `views.py` renders the sidebar and progress tracking.

**Session state** lives in `AppSession` (`session.py`), which holds the active OpenAI client, ChromaDB connections, selected language, and module-specific state (e.g., `IndianaJonesAgentSession`).

### Backend (`mr_injector/backend/`)

- **`llm.py`** — All LLM API calls go through `llm_call()` (OpenAI/Azure) or `open_service_llm_call()` (OpenRouter). Client creation via `create_open_ai_client()`.
- **`db.py`** — ChromaDB setup with persistent storage in `chroma_db/`. Uses either OpenAI embeddings (`text-embedding-ada-002`) or local `all-MiniLM-L6-v2` depending on `USE_OPEN_AI_EMBEDDINGS` env var.
- **`rag.py`** — Document parsing (VDI docs, science papers, resumes) and Jinja2-based context formatting for RAG prompts.
- **`agent.py`** — Agent implementations for the agent security modules.
- **`mcp_server.py`** — FastMCP server setup.
- **`models/`** — Pydantic models: `documents.py` (document types), `llms.py` (model enums: `OpenAIModels`, `OpenRouterModels`), `db.py` (collection definitions).

### Data Flow

1. User submits input in a Streamlit module
2. Module calls `llm_call()` or `open_service_llm_call()` with a system prompt + user message
3. For RAG modules, documents are fetched from ChromaDB via `backend/db.py` and formatted via `backend/rag.py`
4. Response is rendered back in the Streamlit UI

### Environment Variables

Copy `.env.template` to `.env` and configure:
- `OPENAI_API_KEY` — Required for most modules
- `AZURE_OPENAI_ENDPOINT` / `AZURE_OPENAI_API_KEY` — For Azure OpenAI
- `OPENROUTER_API_KEY` — For OpenRouter models (Llama, DeepSeek, Gemini, etc.)
- `TAVILY_API_KEY` — For agent web search tools
- `USE_OPEN_AI_EMBEDDINGS` — Set to use OpenAI embeddings instead of local sentence-transformers
- `PRESENTATION_MODE` — Hides certain UI elements for live demos
- `DEBUG` — Enables debug output

### Adding a New Module

1. Create `mr_injector/frontend/modules/module_<name>.py` with a class inheriting `ModuleView`
2. Add the module name to `ModuleNames` enum in `session.py`
3. Register the module instance in `AppSession.modules`
4. Add the module to the navigation structure in `main.py`