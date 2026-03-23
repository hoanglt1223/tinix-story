---
status: completed
created: 2026-03-23
branch: main
---

# UI/UX Redesign — "Warm Book" Theme

## Context
- Brainstorm: `../reports/brainstorm-260323-1009-ui-ux-redesign.md`
- Decisions: drop dark mode, warm neutral palette, smart defaults, tab consolidation 7→4

## Phases

| # | Phase | Status | Files | Complexity |
|---|-------|--------|-------|-----------|
| 1 | [CSS + Header/Footer](phase-01-css-redesign.md) | completed | `custom.css`, `app.py` | Medium |
| 2 | [Settings Smart Defaults](phase-02-settings-redesign.md) | completed | `settings_tab.py`, `core/config.py` | High |
| 3 | [Tab Consolidation](phase-03-tab-consolidation.md) | completed | `continue_tab.py`, `rewrite_tab.py`, `polish_tab.py`, `export_tab.py`, `projects_tab.py`, `app.py` | Medium |
| 4 | [i18n + Polish](phase-04-i18n-polish.md) | completed | `locales/VI/messages.json`, `locales/EN/messages.json`, all UI files | Low |

## Dependencies
- Phase 1 → independent (start here)
- Phase 2 → independent (can parallel with Phase 1)
- Phase 3 → after Phase 1 (needs new CSS classes)
- Phase 4 → after Phase 2 + 3 (cleanup pass)

## Key Risks
1. Gradio CSS specificity wars — test each change against Gradio defaults
2. Smart API detection false positives — always show manual override
3. Tab merge losing functionality — audit every event handler before removing files
