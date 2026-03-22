---
phase: 4
status: pending
priority: P1
tasks: [15, 12, 13]
effort: Medium
depends_on: [phase-01]
---

# Phase 4: UX Polish

## Overview
Improve user experience with live streaming generation, visual project dashboard, and chapter management. These make existing features feel more polished and professional.

## Context Links
- [Plan Overview](plan.md)
- API client streaming: `services/api_client.py` → `generate_stream()`
- Projects tab: `ui/projects_tab.py`
- Continue tab: `ui/continue_tab.py`
- Create tab: `ui/create_tab.py`

---

## Task 15: Generation Progress Live View

### Requirements
- Real-time streaming during chapter generation
- Text appears progressively instead of waiting for full response
- Progress indicator: "Generating chapter 3/20... 2,450 words"
- `generate_stream()` already exists in APIClient — wire to UI

### Related Code Files
- **Modify:** `services/novel_generator.py` — add streaming variants of generate methods
- **Modify:** `ui/create_tab.py` — wire streaming to chapter generation display
- **Modify:** `ui/continue_tab.py` — wire streaming to continuation display
- **Modify:** `locales/*/messages.json`

### Implementation Steps
1. In `novel_generator.py`, add `generate_chapter_stream(project, chapter_num, ...)`:
   - Build same prompt as `generate_chapter()`
   - Call `api_client.generate_stream(messages)` instead of `generate()`
   - Yield accumulated text as each chunk arrives
   - On completion: save full content to DB, update word count
2. In `ui/create_tab.py` and `ui/continue_tab.py`:
   - Change chapter output textbox to use Gradio streaming pattern
   - Button click → generator function → `gr.Textbox.update()` per yield
   - Add word count label that updates with each chunk
   - Add "Generating chapter X/Y..." progress label
3. Ensure stop button (`app_state.stop_requested`) works with streaming

### Success Criteria
- [ ] Text appears progressively within 1s of API response start
- [ ] Word count updates in real-time
- [ ] Progress shows current chapter number
- [ ] Stop button interrupts streaming
- [ ] Final content saved correctly to DB

---

## Task 12: Project Dashboard

### Requirements
- Visual overview replacing plain project list
- Progress bars per project (completed/total chapters)
- Total word counts, creation dates
- Quick actions: continue, export, delete

### Related Code Files
- **Modify:** `ui/projects_tab.py` — redesign with visual elements
- **Modify:** `services/project_manager.py` — add `get_project_stats()`
- **Modify:** `locales/*/messages.json`

### Implementation Steps
1. Add `get_project_stats()` to ProjectManager:
   - Query: project title, genre, total chapters, completed chapters, total words, created_at, updated_at
   - Return list of stat dicts
2. Redesign `ui/projects_tab.py`:
   - Replace Dataframe with card-based layout using `gr.Row()`/`gr.Column()`
   - Each project card shows:
     - Title + genre badge
     - Progress bar: `gr.Slider(interactive=False)` showing completion %
     - Stats: "12,450 words | 5/20 chapters | Created: 2026-03-15"
     - Buttons row: Continue | Export | Delete
   - For scalability: limit to 20 most recent projects, add "Load More"
3. Alternative (simpler): enhance Dataframe with computed progress column, keep tabular but add visual indicators via HTML markdown
4. Add i18n keys for dashboard labels

### Success Criteria
- [ ] Visual progress indicators per project
- [ ] Word count and chapter stats visible at glance
- [ ] Quick action buttons work correctly
- [ ] Responsive layout for different screen widths
- [ ] Handles 50+ projects without slowdown

---

## Task 13: Chapter Reorder & Management

### Requirements
- Reorder chapters (update num field in DB)
- Insert new blank chapter between existing
- Delete individual chapters with auto-renumbering
- Optional: merge/split chapters

### Related Code Files
- **Modify:** `services/project_manager.py` — add chapter management methods
- **Modify:** `ui/projects_tab.py` — add chapter management UI (extend Phase 1 chapter editor)
- **Modify:** `locales/*/messages.json`

### Implementation Steps
1. Add to ProjectManager:
   - `reorder_chapter(project_id, old_num, new_num)`:
     - Shift chapters between old_num and new_num up/down by 1
     - Update target chapter to new_num
     - Use transaction for atomicity
   - `insert_chapter(project_id, after_num, title, desc)`:
     - Shift all chapters where num > after_num up by 1
     - INSERT new chapter at after_num + 1
   - `delete_chapter(project_id, chapter_num)`:
     - DELETE chapter
     - Shift all chapters where num > chapter_num down by 1
   - `merge_chapters(project_id, num1, num2)`:
     - Concatenate content of num1 and num2
     - Delete num2, update num1 content
     - Renumber remaining
2. UI in projects_tab.py chapter editor section:
   - "Move Up" / "Move Down" buttons next to chapter selector
   - "Insert Chapter After" button + title/desc inputs
   - "Delete Chapter" button with confirmation
   - "Merge with Next" button

### Success Criteria
- [ ] Reorder preserves all chapter content
- [ ] Insert creates blank chapter at correct position
- [ ] Delete removes chapter and renumbers correctly
- [ ] All operations atomic (no partial state on failure)
- [ ] Continue tab reflects updated chapter order

---

## Risk Assessment
- **Streaming**: Gradio streaming requires specific component patterns — test with `gr.Textbox` + generator yield
- **Dashboard**: generating HTML in Gradio Markdown is limited — may need `gr.HTML` for richer display
- **Chapter reorder**: DB operations must be transactional — use `conn.execute("BEGIN")` / `conn.commit()` explicitly

## Next Steps
After Phase 4: Phase 5 (Advanced Tools) builds on the polished UX foundation.
