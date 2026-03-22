---
phase: 1
status: complete
priority: P0-P2
tasks: [11, 5, 4, 14]
effort: Low
---

# Phase 1: Foundation & Quick Wins

## Overview
Low-effort, high-value features that lay groundwork for later phases. Chapter editor is prerequisite for AI gap filler (Phase 2). Batch summarizer improves continuation quality. Style matcher feeds into AI analyzer.

## Context Links
- [Brainstorm Report](../reports/brainstorm-260322-2247-20-feature-tasks.md)
- [Plan Overview](plan.md)
- DB schema: `core/database.py`
- Projects tab: `ui/projects_tab.py`
- Novel generator: `services/novel_generator.py`
- Style manager: `services/style_manager.py`

---

## Task 11: Chapter Editor

### Requirements
- Edit chapter content inline in Projects tab
- Save edits to DB (chapters table, content + word_count columns)
- Live word count display
- Unsaved changes warning

### Architecture
No new files. Extend existing `ui/projects_tab.py` and `services/project_manager.py`.

### Related Code Files
- **Modify:** `ui/projects_tab.py` — add chapter selector dropdown, textbox editor, save button
- **Modify:** `services/project_manager.py` — add `update_chapter_content(project_id, chapter_num, content)` method
- **Modify:** `locales/EN/messages.json`, `locales/VI/messages.json` — add editor i18n keys

### Implementation Steps
1. Add `update_chapter_content()` to `ProjectManager` — UPDATE chapters SET content=?, word_count=?, updated_at=? WHERE project_id=? AND num=?
2. In `ui/projects_tab.py`, add accordion section "Chapter Editor":
   - Dropdown: select project → populate chapter dropdown
   - Dropdown: select chapter → load content into `gr.Textbox(interactive=True, lines=20)`
   - `gr.Number` showing live word count (update on change)
   - Save button → calls `update_chapter_content()`, shows status
3. Add i18n keys: `projects.editor_header`, `projects.select_chapter`, `projects.save_chapter`, `projects.save_success`, `projects.word_count`
4. Wire Gradio events: project_selector.change → load chapters, chapter_selector.change → load content, save_btn.click → save

### Success Criteria
- [x] Can select project + chapter, see content
- [x] Can edit content, word count updates
- [x] Save persists to DB, reloads correctly
- [x] i18n works for VI and EN

---

## Task 5: AI Chapter Summarizer (Batch)

### Requirements
- One-click generate summaries for ALL chapters of a project
- Store in existing `chapter_summaries` table
- Progress indicator per chapter
- Used by Continue tab for context memory

### Architecture
Add method to `services/novel_generator.py`. Wire from UI.

### Related Code Files
- **Modify:** `services/novel_generator.py` — add `batch_generate_summaries(project_id)` generator function
- **Modify:** `ui/continue_tab.py` — add "Generate All Summaries" button
- **Modify:** `locales/*/messages.json` — add summary i18n keys

### Implementation Steps
1. In `novel_generator.py`, add `batch_generate_summaries(project_id)`:
   - Load all chapters with content from DB
   - For each chapter without existing summary: call `generate_chapter_summary()` (already exists)
   - Yield progress string: "Summarizing chapter {n}/{total}..."
   - Store each summary in chapter_summaries table
2. In `ui/continue_tab.py`, add button in Accordion section 2:
   - "Generate All Summaries" button
   - Progress textbox showing current status
   - Wire: btn.click → batch_generate_summaries (use gr.update for streaming progress)
3. Add i18n keys: `continue_tab.batch_summary_btn`, `continue_tab.summary_progress`, `continue_tab.summary_complete`

### Success Criteria
- [x] Button generates summaries for all chapters with content
- [x] Skips chapters that already have summaries
- [x] Progress updates visible in UI
- [x] Summaries appear in chapter_summaries table

---

## Task 4: AI Style Matcher

### Requirements
- Analyze uploaded text → identify writing style characteristics
- Create custom StyleProfile saved to `data/writing_styles.json`
- Apply matched style to generation

### Architecture
New service method in `services/style_manager.py`. New UI section in settings or rewrite tab.

### Related Code Files
- **Modify:** `services/style_manager.py` — add `analyze_style(text)` method
- **Modify:** `services/api_client.py` — used for AI call
- **Modify:** `ui/settings_tab.py` — add "Analyze Style from Text" section
- **Modify:** `locales/*/messages.json`

### Implementation Steps
1. In `style_manager.py`, add `analyze_style(text: str) -> dict`:
   - Build prompt: "Analyze this text and describe the writing style in terms of: tone, vocabulary level, sentence structure, pacing, emotional register. Output as JSON: {name, description}"
   - Call `get_api_client().generate()` with the prompt
   - Parse JSON response → return style dict
2. Add `save_analyzed_style(name, description)` — appends to writing_styles.json
3. In `ui/settings_tab.py`, add accordion "Style Analyzer":
   - `gr.Textbox(lines=10)` for pasting sample text
   - "Analyze Style" button
   - Result display showing detected style
   - "Save as Custom Style" button with name input
4. Add i18n keys: `settings.style_analyzer_header`, `settings.analyze_style_btn`, `settings.style_result`, `settings.save_style_btn`

### Success Criteria
- [x] Paste text → get style analysis
- [x] Save creates new entry in writing_styles.json
- [x] New style appears in style dropdowns across all tabs
- [x] Works with both short (500 word) and long (10k word) samples

---

## Task 14: Dark Mode & Theme System

### Requirements
- Toggle dark/light mode via settings
- CSS variables in custom.css
- Persist preference in config table

### Related Code Files
- **Modify:** `custom.css` — add CSS variables for colors, dark mode class
- **Modify:** `ui/settings_tab.py` — add theme toggle
- **Modify:** `core/config.py` — persist theme preference
- **Modify:** `app.py` — apply theme on load
- **Modify:** `locales/*/messages.json`

### Implementation Steps
1. Refactor `custom.css` to use CSS variables: `--bg-primary`, `--text-primary`, `--accent`, etc.
2. Add `.dark-mode` class that overrides all variables
3. In `ui/settings_tab.py`, add toggle: `gr.Radio(["Light", "Dark"], value="Light")`
4. On toggle change: save to config table (key="theme"), apply via `gr.HTML` JavaScript injection
5. On app load in `app.py`: read theme from config, apply class

### Success Criteria
- [x] Toggle switches between light/dark
- [x] Preference persists across restarts
- [x] All UI elements readable in both modes
- [x] No broken styling in any tab

---

## Risk Assessment
- **Low risk overall** — all tasks modify existing files with small additions
- Chapter editor: ensure concurrent edits don't corrupt (use DB transactions)
- Style matcher: AI output parsing may fail → add fallback for non-JSON responses
- Dark mode: Gradio components have own styling → may need `!important` overrides

## Next Steps
After Phase 1: proceed to Phase 2 (AI Core) — chapter editor enables gap filler testing.
