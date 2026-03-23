# Phase 3: Tab Consolidation (7 → 4)

## Priority: Medium | Status: Completed

## Overview
Merge Rewrite + Polish into Continue tab as sub-actions. Merge Export into Projects tab. Result: 4 tabs (Create, Continue, Projects, Settings).

## Related Files
- **Modify:** `ui/continue_tab.py`, `ui/projects_tab.py`, `app.py`
- **Delete (eventually):** `ui/rewrite_tab.py`, `ui/polish_tab.py`, `ui/export_tab.py`

## Architecture

### Current: 7 Tabs
Create | Continue | Rewrite | Polish | Export | Projects | Settings

### New: 4 Tabs
Create | Continue | Projects | Settings

### Merge Strategy

#### A. Rewrite + Polish → Continue Tab
**Rationale:** Rewrite (68 lines) and Polish (63 lines) are simple "process text" operations — same pattern as Continue. They're contextually related: user works on a chapter, then may want to rewrite or polish it.

**Implementation:**
Add a new accordion at bottom of continue_tab.py:

```python
with gr.Accordion(t("continue_tab.text_tools"), open=False):
    tool_mode = gr.Radio(
        choices=[t("tabs.rewrite"), t("tabs.polish")],
        value=t("tabs.rewrite"),
        label=t("continue_tab.tool_mode")
    )
    # Shared inputs
    tool_file_input = gr.File(label=t("rewrite.upload_file"), file_types=[".txt", ".docx", ".md", ".pdf"])
    tool_text_input = gr.Textbox(label=t("polish.original_text"), lines=8)

    # Rewrite-specific
    with gr.Row(visible=True) as rewrite_options:
        tool_genre = gr.Dropdown(choices=genre_choices, ...)
        tool_style = gr.Dropdown(choices=style_choices, ...)

    # Polish-specific
    tool_custom_req = gr.Textbox(label=t("polish.custom_req"), visible=False)

    tool_reflection = gr.Checkbox(label=t("continue_tab.self_reflection"), value=False)

    with gr.Row():
        tool_run_btn = gr.Button(t("continue_tab.run_tool"), variant="primary")
        tool_suggest_btn = gr.Button(t("polish.polish_suggest_btn"), visible=False)

    tool_status = gr.Textbox(interactive=False)
    tool_output = gr.Textbox(lines=12, interactive=True, elem_classes=["novel-text"])
```

**Visibility toggling:** `tool_mode.change()` shows/hides rewrite vs polish specific fields.

**Handler:** Single `on_tool_run()` that dispatches to `gen.rewrite_paragraph()` or `gen.polish_text()` based on mode.

#### B. Export → Projects Tab
**Rationale:** Export is a per-project action. Users already select a project in Projects tab — no need to select again in a separate tab.

**Implementation:**
Add export section to `projects_tab.py` after project management:

```python
with gr.Accordion(f"📤 {t('export.header')}", open=False):
    export_project_selector = gr.Dropdown(...)  # reuse project selector
    export_format = gr.Radio(choices=[...])
    export_btn = gr.Button(t("projects.export_btn"), variant="primary")
    export_status = gr.Textbox(interactive=False)
    export_download = gr.File(interactive=False)

    # EPUB Import sub-section
    with gr.Accordion(t("epub_import.header"), open=False):
        # ... existing epub import UI
```

Move all export logic (on_export, on_epub_import functions) from export_tab.py to projects_tab.py.

### C. Update app.py
Remove imports for build_rewrite_tab, build_polish_tab, build_export_tab. Keep only 4 tab builders:

```python
build_create_tab()
build_continue_tab()
build_projects_tab()
build_settings_tab()
```

### D. Cleanup Old Files
After confirming everything works:
- Delete `ui/rewrite_tab.py`
- Delete `ui/polish_tab.py`
- Delete `ui/export_tab.py`

## Todo
- [x] Add Rewrite+Polish accordion to continue_tab.py
- [x] Implement mode toggle (rewrite/polish) with visibility switching
- [x] Port rewrite logic (on_rewrite) into continue_tab
- [x] Port polish logic (on_polish, on_polish_suggest) into continue_tab
- [x] Move export section to projects_tab.py
- [x] Port export logic + EPUB import into projects_tab
- [x] Update app.py: remove 3 tab imports, keep 4 tabs
- [x] Test: rewrite from continue tab works
- [x] Test: polish from continue tab works
- [x] Test: export from projects tab works
- [x] Test: EPUB import from projects tab works
- [x] Delete old files: rewrite_tab.py, polish_tab.py, export_tab.py

## Success Criteria
- 4 tabs total, zero lost functionality
- All event handlers work identically to before
- No orphan i18n keys (verify both locale files)

## Risks
- continue_tab.py already 724 lines → adding ~130 lines pushes to ~850. Consider extracting tool section to `ui/text_tools.py` helper module if needed.
- projects_tab.py 494 lines → adding ~160 lines from export. Manageable but monitor.
