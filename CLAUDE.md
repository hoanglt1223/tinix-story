# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TiniX Story 1.0 is an AI-powered novel generation system built with Python + Gradio. It supports creating, continuing, rewriting, and polishing long-form fiction using multiple LLM backends. The primary language of code comments and UI strings is Vietnamese, with i18n support.

## Commands

```bash
# Run the app (launches Gradio on port 7860 by default)
python app.py

# Run with Vietnamese UI (default)
APP_LANGUAGE=VI python app.py

# Run with English UI
APP_LANGUAGE=EN python app.py

# Install dependencies
pip install -r requirements.txt

# Docker
docker compose up --build
```

There are no test suites or linters configured in this project.

## Architecture

### Entry Point
`app.py` — creates the Gradio UI with 7 tabs (create, continue, rewrite, polish, export, projects, settings) and launches the web server.

### Layer Structure

```
core/           — Singleton config, SQLite database, logging, shared app state
services/       — Business logic (API calls, novel generation, project/genre management)
ui/             — Gradio tab builders (one file per tab)
utils/          — File parsing, export (docx/txt/md/html)
locales/        — i18n with nested JSON files (EN/, VI/)
data/           — Static JSON data (genres, sub-genres, writing styles)
```

### Key Singletons & Access Patterns

- **ConfigManager** (`core/config.py`): `get_config()` — manages API backends and generation params, persists to SQLite
- **Database** (`core/database.py`): `get_db()` — libsql connection (local SQLite or Turso cloud via env vars) at `data/tinix_story.db`
- **APIClient** (`services/api_client.py`): `get_api_client()` — wraps OpenAI SDK for all LLM providers, includes response cache, rate limiter, retry with backoff, and round-robin load balancing across backends
- **AppState** (`core/state.py`): `app_state` — thread-safe shared state for generation status across UI tabs
- **i18n** (`locales/i18n.py`): `t("dotted.key")` — all user-facing strings use this; language set via `APP_LANGUAGE` env var

### Data Flow

1. UI tabs in `ui/` call service functions from `services/`
2. `NovelGenerator` (`services/novel_generator.py`) orchestrates chapter generation — builds prompts with genre/style/outline context, calls `APIClient.generate()`, saves to SQLite
3. `APIClient` routes requests through configured backends (OpenAI-compatible API format for all providers), handles caching/retry/rate-limiting
4. All persistent data (config, projects, chapters, cache) lives in SQLite (`data/tinix_story.db`)

### API Backend System

All LLM providers (OpenAI, Anthropic, Google, DeepSeek, Groq, etc. — 20+ providers) are accessed via the OpenAI Python SDK with custom `base_url`. Backend configs are stored in the `backends` SQLite table. The `API_PROVIDERS` dict in `core/config.py` defines provider metadata.

### Novel Generation Pipeline

`NovelGenerator` handles: title generation → character/world building → outline creation → chapter-by-chapter generation with self-reflection/critique loop. Generation cache and chapter summaries are persisted to SQLite for resume capability.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `APP_LANGUAGE` | `VI` | UI language (`VI`, `EN`) |
| `NOVEL_TOOL_HOST` | `0.0.0.0` | Server bind host |
| `NOVEL_TOOL_PORT` | `7860` | Server port |
| `NOVEL_TOOL_SHARE` | `false` | Gradio public share link |
| `TURSO_DATABASE_URL` | _(empty)_ | Turso cloud DB URL. If set, uses Turso; otherwise local SQLite file |
| `TURSO_AUTH_TOKEN` | _(empty)_ | Turso auth token |

## Conventions

- Code comments and log messages are in Vietnamese
- All user-facing strings go through `t()` from `locales/i18n.py`, never hardcoded
- Singletons use module-level `_instance` pattern with `get_*()` accessor functions
- Database operations use raw SQL with `libsql_experimental` SDK (SQLite-compatible, supports Turso cloud)
- File naming uses snake_case for Python modules
