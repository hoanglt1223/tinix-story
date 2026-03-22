---
phase: 6
status: pending
priority: P2
tasks: [18, 20]
effort: Medium
depends_on: [phase-04]
---

# Phase 6: Extras

## Overview
Nice-to-have features for power users. Multi-model comparison helps quality optimization. Version history prevents accidental content loss during regeneration.

## Context Links
- [Plan Overview](plan.md)
- API client: `services/api_client.py`
- Novel generator: `services/novel_generator.py`
- DB schema: `core/database.py`

---

## Task 18: Multi-Model Comparison

### Requirements
- Generate same chapter with 2-3 different backends/models simultaneously
- Side-by-side comparison view
- User picks best version → saves as final

### Related Code Files
- **Modify:** `services/novel_generator.py` — add `generate_chapter_multi(project, chapter_num, backend_names)`
- **Modify:** `ui/continue_tab.py` — add comparison UI
- **Modify:** `locales/*/messages.json`

### Implementation Steps
1. In `novel_generator.py`, add `generate_chapter_multi()`:
   - Build prompt once (same as regular generate)
   - For each selected backend: create temp APIClient, call generate()
   - Return dict: {backend_name: generated_content}
   - Use threading for parallel generation
2. UI in continue_tab.py:
   - Checkbox: "Enable Multi-Model Comparison"
   - When enabled: show backend multi-select (from enabled backends)
   - After generation: show results in side-by-side `gr.Textbox` columns
   - "Select Version" radio per result → "Save Selected" button
3. Display word count and generation time per version

### Success Criteria
- [ ] Generates with 2-3 models in parallel
- [ ] Side-by-side display readable
- [ ] Selected version saves correctly
- [ ] Shows generation time per model for comparison
- [ ] Handles backend failure gracefully (show error for failed, results for successful)

---

## Task 20: Chapter Version History

### Requirements
- Keep previous versions when regenerating a chapter
- New DB table: `chapter_versions`
- View previous versions, rollback to any

### DB Schema
```sql
CREATE TABLE IF NOT EXISTS chapter_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    chapter_num INTEGER NOT NULL,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    word_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
```

### Related Code Files
- **Modify:** `core/database.py` — add `chapter_versions` table
- **Create:** `services/version_manager.py` (~80 lines)
- **Modify:** `services/novel_generator.py` — save version before overwriting chapter
- **Modify:** `ui/projects_tab.py` — add version history to chapter editor
- **Modify:** `locales/*/messages.json`

### Implementation Steps
1. Add table to `init_db()`
2. Create `services/version_manager.py`:
   - `save_version(project_id, chapter_num, content, word_count)`:
     - Get max version for this chapter → increment
     - INSERT into chapter_versions
   - `list_versions(project_id, chapter_num) -> List[dict]`:
     - Return all versions ordered by version desc
   - `get_version(project_id, chapter_num, version) -> str`:
     - Return content for specific version
   - `rollback(project_id, chapter_num, version)`:
     - Save current as new version first
     - Copy target version content to chapters table
3. Modify `novel_generator.py`:
   - Before writing new chapter content, call `save_version()` with existing content (if any)
4. UI in projects_tab.py chapter editor:
   - "Version History" dropdown showing versions with dates
   - "View" button → loads version content in read-only textbox
   - "Rollback to This Version" button with confirmation
   - Version count badge next to chapter selector

### Success Criteria
- [ ] Every regeneration creates a version entry
- [ ] Version list shows dates and word counts
- [ ] Rollback restores content correctly
- [ ] Current version always preserved before rollback
- [ ] Works with chapter editor (Task 11)

---

## Risk Assessment
- **Multi-Model**: parallel API calls may hit rate limits → stagger by 1s between calls
- **Version History**: storage growth — old versions accumulate → add optional cleanup (keep last N versions)
- **Both**: these are P2 features — implement after core features are stable

## Next Steps
After Phase 6: all 20 features complete. Focus shifts to testing, documentation, and polish.
