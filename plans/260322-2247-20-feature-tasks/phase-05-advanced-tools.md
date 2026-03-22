---
phase: 5
status: pending
priority: P1-P2
tasks: [3, 17, 19]
effort: Medium
depends_on: [phase-02]
---

# Phase 5: Advanced Tools

## Overview
Power-user features for quality assurance, visual editing, and cost management. Consistency checker leverages AI analysis patterns from Phase 2. Outline editor improves authoring workflow. Cost tracker adds production awareness.

## Context Links
- [Plan Overview](plan.md)
- Novel generator: `services/novel_generator.py`
- API client: `services/api_client.py`
- Create tab: `ui/create_tab.py`
- Settings tab: `ui/settings_tab.py`

---

## Task 3: AI Consistency Checker

### Requirements
- Scan full novel for: character name variations, timeline contradictions, plot holes, tone shifts
- Report with chapter references and severity levels
- Suggest fixes

### Architecture
New service: `services/consistency_checker.py` (~150 lines). Report displayed in UI.

### Related Code Files
- **Create:** `services/consistency_checker.py`
- **Modify:** `ui/projects_tab.py` — add "Check Consistency" button and report display
- **Modify:** `locales/*/messages.json`

### Implementation Steps
1. Create `services/consistency_checker.py`:
   ```python
   class ConsistencyChecker:
       def check_project(self, project_id) -> List[dict]:
           """Returns list of {type, severity, chapter, description, suggestion}"""
           chapters = self._load_all_chapters(project_id)
           characters = self._load_characters(project_id)  # from character bible
           issues = []
           # Check in chunks (2-3 chapters per AI call)
           for chunk in self._chunk_chapters(chapters, size=3):
               chunk_issues = self._check_chunk(chunk, characters)
               issues.extend(chunk_issues)
           # Cross-chapter checks
           issues.extend(self._check_cross_chapter(chapters))
           return sorted(issues, key=lambda x: x["severity"], reverse=True)
   ```
2. `_check_chunk()`: prompt AI to find inconsistencies within consecutive chapters
3. `_check_cross_chapter()`: prompt AI with character list + chapter summaries to find arc issues
4. Issue types: `name_variation`, `timeline_error`, `plot_hole`, `tone_shift`, `missing_resolution`
5. Severity: `critical`, `warning`, `info`
6. UI: button in Projects tab → generates report → display as formatted Markdown or Dataframe

### Success Criteria
- [ ] Detects obvious name inconsistencies (e.g., "John" vs "Jon")
- [ ] Reports include chapter numbers and context
- [ ] Severity levels help prioritize fixes
- [ ] Handles novels with 20+ chapters without timeout

---

## Task 17: Outline Visual Editor

### Requirements
- Card-based view of outline chapters
- Edit chapter descriptions inline
- Better than raw text editing

### Architecture
Enhance existing outline display in Create/Continue tabs. Use Gradio components for card layout.

### Related Code Files
- **Modify:** `ui/create_tab.py` — replace text outline with visual editor
- **Modify:** `services/novel_generator.py` — add outline CRUD methods
- **Modify:** `locales/*/messages.json`

### Implementation Steps
1. Add to `novel_generator.py`:
   - `update_chapter_outline(project_id, chapter_num, title, desc)` — UPDATE chapters SET title=?, desc=?
   - `add_outline_chapter(project_id, num, title, desc)` — INSERT into chapters
   - `remove_outline_chapter(project_id, num)` — DELETE + renumber
2. In `ui/create_tab.py`, after outline generation:
   - Display chapters as list of `gr.Accordion` elements, each containing:
     - Chapter number + title (editable `gr.Textbox`)
     - Description (editable `gr.Textbox`, lines=3)
     - Save/Delete buttons
   - "Add Chapter" button at bottom
   - Note: Gradio doesn't support dynamic component creation easily → use fixed max slots (e.g., 50) with visibility toggle
3. Alternative simpler approach: use `gr.Dataframe(interactive=True)` with columns [Num, Title, Description] — user edits cells directly, "Save All" button commits changes

### Success Criteria
- [ ] Can edit chapter titles and descriptions inline
- [ ] Can add/remove chapters from outline
- [ ] Changes persist to DB
- [ ] Generated chapters use updated outline data

---

## Task 19: Token & Cost Tracker

### Requirements
- Track API token usage per project, per backend
- New DB table: `api_usage`
- Show estimated cost in dashboard
- Optional budget alerts

### DB Schema
```sql
CREATE TABLE IF NOT EXISTS api_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT,
    backend_name TEXT NOT NULL,
    model TEXT NOT NULL,
    tokens_in INTEGER NOT NULL DEFAULT 0,
    tokens_out INTEGER NOT NULL DEFAULT 0,
    cost_estimate REAL NOT NULL DEFAULT 0.0,
    operation TEXT NOT NULL DEFAULT 'generate',
    created_at TEXT NOT NULL
);
```

### Related Code Files
- **Modify:** `core/database.py` — add `api_usage` table
- **Create:** `services/cost_tracker.py` (~100 lines)
- **Modify:** `services/api_client.py` — log usage after each API call
- **Modify:** `ui/settings_tab.py` — add cost dashboard section
- **Modify:** `locales/*/messages.json`

### Implementation Steps
1. Add table to `init_db()`
2. Create `services/cost_tracker.py`:
   - `log_usage(project_id, backend, model, tokens_in, tokens_out, operation)`
   - `get_project_costs(project_id) -> dict` — total tokens, estimated cost
   - `get_total_costs() -> dict` — aggregate across all projects
   - Cost estimation: hardcoded price table per model family (e.g., GPT-4o: $2.50/1M input, $10/1M output)
3. Modify `api_client.py` `generate()` method:
   - After successful response, extract `response.usage.prompt_tokens` and `response.usage.completion_tokens`
   - Call `cost_tracker.log_usage()`
4. UI in settings tab:
   - "Cost Dashboard" accordion
   - Total tokens used, estimated cost
   - Per-project breakdown table
   - Per-backend breakdown

### Success Criteria
- [ ] Every API call logged with token counts
- [ ] Cost estimates visible in settings
- [ ] Per-project breakdown works
- [ ] Handles responses without usage data gracefully (some providers omit it)

---

## Risk Assessment
- **Consistency Checker**: quality depends heavily on LLM — may produce false positives. Show disclaimer in UI
- **Outline Editor**: Gradio's dynamic component limitations → use Dataframe approach if accordion approach is too complex
- **Cost Tracker**: token counts vary by provider format → add try/except around usage extraction

## Next Steps
After Phase 5: Phase 6 (Extras) for multi-model comparison and version history.
