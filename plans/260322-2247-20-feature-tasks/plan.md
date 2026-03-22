---
status: in_progress
created: 2026-03-22
scope: 20 feature tasks across 6 phases
brainstorm: plans/reports/brainstorm-260322-2247-20-feature-tasks.md
estimated_phases: 6
---

# TiniX Story — 20 Feature Implementation Plan

## Overview
Implement 20 features across AI analysis, import/export, UI/UX, and power tools. Organized into 6 phases by dependency and priority.

## Phase Summary

| Phase | Theme | Tasks | Priority | Key Deliverables |
|-------|-------|-------|----------|-----------------|
| [Phase 1](phase-01-foundation.md) ✓ | Foundation & Quick Wins | #11, #5, #4, #14 | P0-P2 | Chapter editor, batch summarizer, style matcher, dark mode |
| [Phase 2](phase-02-ai-core.md) | AI Core Intelligence | #1, #2, #16 | P0 | Novel analyzer, gap filler, character bible |
| [Phase 3](phase-03-import-export.md) | Import/Export | #6, #7, #9, #8, #10 | P0-P2 | Smart EPUB import, EPUB/PDF export, archives, bulk import |
| [Phase 4](phase-04-ux-polish.md) | UX Polish | #15, #12, #13 | P1 | Live streaming, dashboard, chapter management |
| [Phase 5](phase-05-advanced-tools.md) | Advanced Tools | #3, #17, #19 | P1-P2 | Consistency checker, outline editor, cost tracker |
| [Phase 6](phase-06-extras.md) | Extras | #18, #20 | P2 | Multi-model comparison, version history |

## DB Migration Summary
New tables needed across phases:
- `characters` (Phase 2) — character bible per project
- `api_usage` (Phase 5) — token/cost tracking
- `chapter_versions` (Phase 6) — version history

All migrations added to `init_db()` in `core/database.py` using `CREATE TABLE IF NOT EXISTS`.

## Cross-Cutting Concerns
- **i18n**: Every new UI string must use `t()`. Add keys to both `locales/EN/messages.json` and `locales/VI/messages.json`
- **File size**: Keep new modules under 200 lines. Split if needed.
- **Patterns**: Follow existing singleton pattern (`get_*()` functions), raw SQL, Gradio tab builders
- **Testing**: No test suite exists — manual testing via `python app.py`

## Dependencies
```
Phase 1 (foundation) ──→ Phase 2 (AI core) ──→ Phase 3 (import/export)
                                                       │
Phase 4 (UX) ←─────────────────────────────────────────┘
       │
Phase 5 (advanced) ──→ Phase 6 (extras)
```
Phase 1 unblocks Phase 2 (chapter editor needed for gap filler). Phase 3 can run partially parallel with Phase 2. Phases 4-6 are largely independent.
