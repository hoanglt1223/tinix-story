# Code Review: Phase 1 Foundation

**Date:** 2026-03-22 | **Files:** 8 | **Focus:** correctness, security, runtime issues

## Overall Assessment
Solid implementation. SQL queries all parameterized. i18n keys present in both locales. A few bugs and code smells need attention.

## Critical Issues
None found. No SQL injection, no secrets exposure, no auth bypass.

## High Priority

1. **`update_chapter_content` uses `len(content)` for word_count** (`project_manager.py:262`)
   - `len(content)` counts **characters**, not words. Inconsistent with how `word_count` is semantically used elsewhere.
   - Fix: `word_count = len(content.split()) if content else 0`

2. **`continue_tab.py:99` -- `on_continue_project_select` returns 3 values on error, 4 on success** (line 99 vs 148)
   - Error path returns `(str, int, str)` (3 values) but success returns `(str, int, str, list)` (4 values).
   - Gradio expects consistent output count matching `outputs=[..4 items..]`. Will cause runtime error on "project not found" path.
   - Fix: add `[]` as 4th return on line 99: `return f"... ", 1, "Chua tai du an...", []`

3. **Duplicate `gen = app_state.get_generator()` call** (`continue_tab.py:167,171` and `259,263`)
   - `gen` assigned, style set on it, then immediately reassigned from scratch on next line -- style override lost.
   - Fix: remove the second `gen = app_state.get_generator()` call in both functions.

4. **Theme JS injection via `gr.HTML` may not execute** (`settings_tab.py:548`)
   - Gradio sanitizes `<script>` tags in `gr.HTML` value updates. The dark mode toggle script likely won't run at runtime.
   - Consider using `gr.Blocks(js=...)` or Gradio's JS callback param instead.

## Medium Priority

5. **`word_count` inconsistency in `continue_tab.py:224,327`** -- same `len(content)` char-count bug as #1.

6. **Style Analyzer sub-tab and Style Manager sub-tab labels not i18n'd** (`settings_tab.py:410,413,422-430`)
   - Hardcoded Vietnamese strings: "Quan ly phong cach viet", "Ten phong cach", "Mo ta phong cach", etc.
   - Should use `t()` for consistency with rest of app.

7. **`on_editor_content_change` fires on every keystroke** (`projects_tab.py:135`)
   - `editor_textbox.change` triggers a server round-trip per character typed.
   - Consider debouncing or computing word count client-side via JS.

8. **`get_project_by_title` does a full table scan** (`project_manager.py:244`)
   - Calls `list_projects()` which fetches all projects + counts. Inefficient for single lookup.
   - Could use direct SQL: `SELECT id FROM projects WHERE title = ? LIMIT 1`

## Low Priority

9. **Debug print left in** (`settings_tab.py:151`) -- `print(f"DEBUG: on_backend_select triggered with: {selected_name}")` should use logger.

10. **Bare `except:` on line 165** of `project_manager.py` -- should be `except (json.JSONDecodeError, TypeError):`.

11. **Duplicate `select_chapter` key** in both EN and VI locale files (lines 250/255 EN, 357/362 VI) -- second definition silently overwrites first.

## Security Notes
- All SQL uses parameterized queries -- good.
- `analyze_style` truncates input to 5000 chars before sending to LLM -- reasonable guard.
- API keys displayed as `type="text"` in settings (`settings_tab.py:91`) -- consider `type="password"`.

## Positive Observations
- Clean separation: service layer handles DB, UI layer handles Gradio wiring
- Consistent error handling with try/catch + logging throughout
- CSS variables approach for theming is well-structured
- `batch_generate_summaries` correctly skips chapters with existing summaries

## Recommended Actions (priority order)
1. Fix return value mismatch in `on_continue_project_select` (will crash at runtime)
2. Remove duplicate `get_generator()` calls (style override silently lost)
3. Fix `len(content)` -> `len(content.split())` for word counts
4. Replace `<script>` injection with Gradio JS callback for theme toggle
5. i18n remaining hardcoded strings in style manager sub-tab

## Unresolved Questions
- Is `chapter_summaries` table cleaned up when a project is deleted? `delete_project` only deletes from `projects` table -- orphaned summaries may accumulate.
- Is `app_state.current_project` thread-safe for concurrent Gradio users? Multiple users could overwrite each other's project state.
