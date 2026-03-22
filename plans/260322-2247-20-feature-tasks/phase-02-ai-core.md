---
phase: 2
status: pending
priority: P0
tasks: [1, 2, 16]
effort: Medium
depends_on: [phase-01]
---

# Phase 2: AI Core Intelligence

## Overview
Core differentiators — AI novel analysis, gap filling, and character bible. These transform TiniX Story from a generation-only tool into an intelligent writing assistant. Depends on Phase 1 chapter editor for testing gap filler output.

## Context Links
- [Plan Overview](plan.md)
- Novel generator: `services/novel_generator.py`
- API client: `services/api_client.py`
- DB schema: `core/database.py`
- Project manager: `services/project_manager.py`

---

## Task 1: AI Novel Analyzer

### Requirements
- Import novel file → AI extracts: character profiles, world settings, plot structure, writing style, genre
- Auto-fill NovelProject metadata fields
- Handle novels exceeding context window via chunked analysis
- Output: populated character_setting, world_setting, plot_idea, detected genre/sub_genres

### Architecture
New service: `services/novel_analyzer.py` (~150 lines). New UI tab or section in Continue tab.

### Related Code Files
- **Create:** `services/novel_analyzer.py` — chunked analysis engine
- **Modify:** `ui/continue_tab.py` — add "Import & Analyze" section
- **Modify:** `services/project_manager.py` — use analyzed data to create/update project
- **Modify:** `locales/*/messages.json`

### Implementation Steps
1. Create `services/novel_analyzer.py`:
   ```python
   class NovelAnalyzer:
       def analyze_novel(self, text: str) -> dict:
           """Analyze novel text, return {characters, world, plot, genre, sub_genres, style}"""
           chunks = self._chunk_text(text, max_chars=6000)
           # Phase A: analyze each chunk for characters/settings
           chunk_analyses = [self._analyze_chunk(c) for c in chunks[:5]]  # limit to 5 chunks
           # Phase B: merge analyses into unified profile
           merged = self._merge_analyses(chunk_analyses)
           # Phase C: detect genre/style from first 2 chunks
           merged["genre"] = self._detect_genre(chunks[:2])
           return merged
   ```
2. `_chunk_text()`: split by chapter boundaries (reuse `file_parser.py` patterns), fallback to ~6000 char chunks
3. `_analyze_chunk()`: prompt AI to extract characters, settings, plot points from chunk
4. `_merge_analyses()`: prompt AI to merge multiple chunk results into unified metadata
5. `_detect_genre()`: prompt AI to identify genre from writing samples, match against existing genres in `data/genres.json`
6. In `ui/continue_tab.py`, add accordion "Import & Analyze Novel":
   - File upload (reuse existing file upload pattern)
   - "Analyze" button → shows progress → populates metadata fields
   - User reviews/edits extracted data → "Create Project" button
7. Add i18n keys for analyzer UI

### Key Prompt Design
```
Analyze this novel excerpt. Extract:
1. CHARACTER PROFILES: name, role, personality, appearance (JSON array)
2. WORLD SETTING: time period, location, rules, atmosphere
3. PLOT SUMMARY: main conflict, current arc, key events
Return as JSON: {characters: [...], world_setting: "...", plot_summary: "..."}
```

### Success Criteria
- [ ] Upload .txt/.epub → get meaningful character/world/plot extraction
- [ ] Genre detection matches reasonable genre from existing list
- [ ] Works with novels 10k-500k characters (chunking handles large texts)
- [ ] Extracted data can create functional project for continuation
- [ ] Handles non-standard formatting gracefully

---

## Task 2: AI Chapter Gap Filler

### Requirements
- Detect blank/short chapters in existing projects
- AI generates missing content based on surrounding chapters + outline
- Batch mode (fill all) or selective (per-chapter)
- Respects chapter descriptions from outline

### Architecture
Add methods to `services/novel_generator.py`. Wire from Continue tab.

### Related Code Files
- **Modify:** `services/novel_generator.py` — add `detect_gaps()`, `fill_chapter_gap()`, `fill_all_gaps()`
- **Modify:** `ui/continue_tab.py` — add gap detection + fill UI
- **Modify:** `locales/*/messages.json`

### Implementation Steps
1. Add `detect_gaps(project_id) -> List[Chapter]`:
   - Query chapters WHERE content = '' OR word_count < 100
   - Return list of gap chapters with their num, title, desc
2. Add `fill_chapter_gap(project_id, chapter_num, target_words, use_reflection)`:
   - Load project context (surrounding chapters, outline)
   - Build prompt using chapter desc + context (reuse existing `generate_chapter` pattern)
   - Generate content → save to DB
   - Return generated content
3. Add `fill_all_gaps(project_id)` — generator yielding progress per chapter:
   - Call detect_gaps → iterate → fill_chapter_gap each
   - Yield "Filling chapter {n}/{total}..."
4. In `ui/continue_tab.py`, add accordion section "Gap Detection & Fill":
   - "Detect Gaps" button → shows list of empty/short chapters
   - Per-chapter "Fill" button, or "Fill All Gaps" batch button
   - Progress display for batch mode
   - Uses same style/reflection/memory settings as regular continuation

### Success Criteria
- [ ] Correctly identifies blank and short (<100 words) chapters
- [ ] Generated content fits narrative context
- [ ] Batch fill shows progress and saves each chapter
- [ ] Respects outline descriptions for each chapter
- [ ] Chapter editor (Task 11) can review/edit filled content

---

## Task 16: Character Bible

### Requirements
- Per-project character management
- Fields: name, role, appearance, personality, relationships, arc_notes, first_chapter
- New DB table: `characters`
- AI references character bible during generation
- UI in Continue/Create tabs

### Architecture
New service: `services/character_manager.py` (~120 lines). DB migration. New UI component.

### Related Code Files
- **Create:** `services/character_manager.py` — CRUD for characters
- **Modify:** `core/database.py` — add `characters` table to `init_db()`
- **Modify:** `services/novel_generator.py` — inject character context into generation prompts
- **Modify:** `ui/continue_tab.py` — add character bible accordion
- **Modify:** `ui/create_tab.py` — add character bible option
- **Modify:** `locales/*/messages.json`

### DB Schema
```sql
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT '',
    appearance TEXT NOT NULL DEFAULT '',
    personality TEXT NOT NULL DEFAULT '',
    relationships TEXT NOT NULL DEFAULT '',
    arc_notes TEXT NOT NULL DEFAULT '',
    first_chapter INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE(project_id, name)
);
```

### Implementation Steps
1. Add table to `init_db()` in `core/database.py`
2. Create `services/character_manager.py`:
   - `CharacterManager` class with static methods (follow ProjectManager pattern)
   - `add_character(project_id, name, **fields)`
   - `update_character(project_id, name, **fields)`
   - `delete_character(project_id, name)`
   - `list_characters(project_id) -> List[dict]`
   - `get_character_context(project_id) -> str` — formatted string for prompt injection
3. Modify `novel_generator.py` generation prompts:
   - In chapter generation, call `CharacterManager.get_character_context(project_id)`
   - Inject as system prompt section: "CHARACTER BIBLE: {context}"
   - Only inject if characters exist for project
4. UI in `ui/continue_tab.py`:
   - Accordion "Character Bible" with:
   - Dataframe showing existing characters (name, role)
   - Add/Edit form: name, role, appearance, personality, relationships, arc_notes
   - Delete button per character
   - "Auto-Extract from Novel" button (uses Task 1 analyzer if available)

### Success Criteria
- [ ] CRUD characters per project
- [ ] Character context injected into generation prompts
- [ ] Generated chapters reference character names/traits correctly
- [ ] Character data survives project reload
- [ ] Auto-extract populates from existing novel text

---

## Risk Assessment
- **AI Analyzer**: LLM may return invalid JSON → implement robust JSON extraction with regex fallback
- **Gap Filler**: context window limits may truncate surrounding chapters → summarize context if too long
- **Character Bible**: prompt injection of character context adds tokens → budget ~500 tokens for character section
- **All tasks**: smaller/cheaper models may produce poor analysis → warn users in UI

## Next Steps
After Phase 2: Phase 3 (Import/Export) — EPUB import benefits from analyzer. Phase 4 (UX) can start in parallel.
