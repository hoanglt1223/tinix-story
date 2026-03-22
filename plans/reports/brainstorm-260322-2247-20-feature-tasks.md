---
type: brainstorm
date: 2026-03-22
status: approved
scope: 20 feature tasks across 4 categories
---

# Brainstorm: 20 Feature Tasks for TiniX Story

## Problem Statement
TiniX Story 1.0 has solid core generation pipeline but lacks advanced AI analysis, modern UX, rich import/export, and power-user authoring tools. These 20 tasks address the biggest gaps.

## Current State Summary
- 7 UI tabs: Create, Continue, Rewrite, Polish, Export, Projects, Settings
- 5 import formats (txt, pdf, epub, md, docx), 4 export formats (docx, txt, md, html)
- SQLite persistence, multi-backend LLM support (20+ providers)
- Genre/sub-genre/style management system
- Context memory (full text + summaries) for continuation
- Self-reflection generation mode
- Missing: chapter editing, AI analysis, EPUB export, visual dashboards, version history

---

## Category A: AI Analysis & Smart Fill

### Task 1: AI Novel Analyzer
- **Priority:** P0 (Critical)
- **Effort:** Medium
- Import existing novel → AI extracts character profiles, world settings, plot structure, writing style
- Fills NovelProject metadata automatically so user can *continue* the story
- Uses chunked analysis (novel may exceed context window)
- Output: populated character_setting, world_setting, plot_idea, detected genre/sub-genres

### Task 2: AI Chapter Gap Filler
- **Priority:** P0
- **Effort:** Medium
- Detect blank/short chapters in existing projects
- AI generates missing content based on surrounding chapters + outline context
- Batch mode: fill all gaps at once, or selective per-chapter
- Respects existing chapter descriptions from outline

### Task 3: AI Consistency Checker
- **Priority:** P1
- **Effort:** Medium
- Scan full novel for: character name variations, timeline contradictions, plot holes, tone shifts
- Report with chapter references and severity levels
- Suggest fixes inline

### Task 4: AI Style Matcher
- **Priority:** P1
- **Effort:** Low
- Analyze uploaded text → identify writing style, tone, vocabulary level, pacing
- Create custom StyleProfile saved to data/writing_styles.json
- Apply matched style to new generation for consistency

### Task 5: AI Chapter Summarizer (Batch)
- **Priority:** P1
- **Effort:** Low
- One-click generate summaries for ALL chapters of a project
- Store in chapter_summaries table
- Used as context memory during continuation
- Progress indicator per chapter

---

## Category B: Import & Export Enhancements

### Task 6: Smart EPUB Import
- **Priority:** P0
- **Effort:** Medium
- Import EPUB with chapter detection via TOC
- Auto-create project with: parsed chapters, metadata (author, title), cover extraction
- Map EPUB spine to chapter order
- Handle nested TOC structures
- Current parse_epub_file() returns flat text — enhance to return structured chapters

### Task 7: EPUB Export
- **Priority:** P1
- **Effort:** Medium
- Export as properly formatted EPUB 3.0
- Include: metadata, TOC (ncx + nav), CSS styling, chapter separation
- Use ebooklib (already in requirements)

### Task 8: PDF Export
- **Priority:** P2
- **Effort:** Medium
- Professional typography: configurable fonts, margins, headers/footers, page numbers
- Use reportlab or weasyprint
- Chapter title pages, table of contents

### Task 9: Project Archive Import/Export
- **Priority:** P2
- **Effort:** Low
- Export: ZIP containing metadata JSON + chapter files + project settings + generation cache
- Import: restore full project from ZIP
- Enables sharing projects between instances

### Task 10: Bulk Import
- **Priority:** P2
- **Effort:** Low
- Upload multiple files at once
- Options: each file = separate project, or merge all into one project as chapters
- Auto-detect chapter boundaries across files

---

## Category C: UI/UX Improvements

### Task 11: Chapter Editor Tab
- **Priority:** P0
- **Effort:** Low
- Inline chapter editing with save to DB
- Currently chapters appear read-only after generation
- Live word count update, unsaved changes indicator
- Add to existing Projects tab or new dedicated tab

### Task 12: Project Dashboard
- **Priority:** P1
- **Effort:** Medium
- Visual overview: progress bars per project, total word counts
- Generation timeline, genre distribution
- Quick actions: continue, export, delete
- Replace current plain project list

### Task 13: Chapter Reorder & Management
- **Priority:** P1
- **Effort:** Medium
- Reorder chapters (update num field)
- Insert new chapter between existing
- Delete individual chapters with renumbering
- Merge two chapters / split one chapter

### Task 14: Dark Mode & Theme System
- **Priority:** P2
- **Effort:** Low
- Toggle dark/light mode via settings
- Extend custom.css with CSS variables
- Persist preference in config table

### Task 15: Generation Progress Live View
- **Priority:** P1
- **Effort:** Medium
- Real-time streaming during chapter generation
- Text appears word-by-word using generate_stream()
- Progress: "Generating chapter 3/20... 2,450 words"
- Already has generate_stream() in api_client.py — wire to UI

---

## Category D: New Features & Power Tools

### Task 16: Character Bible
- **Priority:** P0
- **Effort:** Medium
- Dedicated character management per project
- Fields: name, appearance, personality, relationships, arc notes, first_appearance_chapter
- New DB table: characters (project_id, name, profile JSON)
- AI references character bible during generation for consistency
- UI: dedicated sub-tab or modal in Create/Continue tabs

### Task 17: Outline Visual Editor
- **Priority:** P1
- **Effort:** Medium
- Tree or card-based view of outline
- Edit chapter descriptions inline
- Mark act/arc boundaries
- Better than raw text editing of outline

### Task 18: Multi-Model Comparison
- **Priority:** P2
- **Effort:** Medium
- Generate same chapter with 2-3 different backends/models
- Side-by-side comparison view
- User picks best version → saves as final
- Useful for quality optimization and model evaluation

### Task 19: Token & Cost Tracker
- **Priority:** P2
- **Effort:** Low
- Track API token usage per project, per backend
- New DB table: api_usage (project_id, backend, tokens_in, tokens_out, cost_estimate, timestamp)
- Show estimated cost dashboard
- Budget alerts configurable in settings

### Task 20: Chapter Version History
- **Priority:** P2
- **Effort:** Medium
- Keep previous versions when regenerating a chapter
- New DB table: chapter_versions (chapter_id, version, content, generated_at)
- Diff view between versions
- Rollback to any previous version

---

## Priority Summary

| Priority | Tasks | Theme |
|----------|-------|-------|
| **P0** | 1, 2, 6, 11, 16 | Core differentiators — AI analysis, smart import, editing, character bible |
| **P1** | 3, 4, 5, 7, 12, 13, 15, 17 | High-value enhancements — consistency, export, dashboard, streaming |
| **P2** | 8, 9, 10, 14, 18, 19, 20 | Nice-to-haves — PDF, archives, dark mode, comparison, versioning |

## Recommended Implementation Order

**Phase 1 (Foundation):** #11 Chapter Editor → #5 Batch Summarizer → #4 Style Matcher
**Phase 2 (AI Core):** #1 AI Novel Analyzer → #2 Gap Filler → #16 Character Bible
**Phase 3 (Import/Export):** #6 Smart EPUB Import → #7 EPUB Export → #9 Project Archive
**Phase 4 (UX Polish):** #15 Live Streaming → #12 Dashboard → #13 Chapter Management
**Phase 5 (Advanced):** #3 Consistency Checker → #17 Outline Editor → #19 Cost Tracker
**Phase 6 (Extras):** #14 Dark Mode → #8 PDF Export → #10 Bulk Import → #18 Multi-Model → #20 Version History

## Success Metrics
- AI Analyzer correctly extracts metadata from 80%+ of imported novels
- EPUB import preserves chapter structure for standard EPUBs
- Chapter editor saves without data loss
- Streaming generation shows real-time text within 1s of API response start
- All features maintain existing i18n support (VI/EN)

## Risks
- AI analysis quality depends heavily on LLM capability (smaller models may fail)
- EPUB format is complex — edge cases in chapter detection
- Streaming UI requires Gradio streaming component support (verify compatibility)
- Character Bible adds complexity to generation prompts (token budget management)
- Multi-model comparison doubles/triples API costs per chapter

## Next Steps
Create detailed implementation plan with phases, file changes, and DB migrations.
