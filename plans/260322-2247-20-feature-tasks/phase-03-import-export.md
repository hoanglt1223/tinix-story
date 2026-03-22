---
phase: 3
status: pending
priority: P0-P2
tasks: [6, 7, 9, 8, 10]
effort: Medium
depends_on: [phase-01]
---

# Phase 3: Import/Export Enhancements

## Overview
Expand file format support. Smart EPUB import (P0) is highest priority — transforms flat epub parsing into structured project creation. EPUB/PDF export and project archives round out the feature set.

## Context Links
- [Plan Overview](plan.md)
- File parser: `utils/file_parser.py`
- Exporter: `utils/exporter.py`
- Export tab: `ui/export_tab.py`

---

## Task 6: Smart EPUB Import

### Requirements
- Import EPUB with chapter detection via TOC (table of contents)
- Auto-create project: title, author, parsed chapters with correct order
- Handle nested TOC, EPUB2 and EPUB3 formats
- Current `parse_epub_file()` returns flat text → enhance to return structured chapters

### Related Code Files
- **Modify:** `utils/file_parser.py` — add `parse_epub_structured()` returning list of ChapterInfo
- **Modify:** `ui/continue_tab.py` or `ui/create_tab.py` — add EPUB import section
- **Modify:** `services/project_manager.py` — add `create_project_from_chapters()`
- **Modify:** `locales/*/messages.json`

### Implementation Steps
1. In `utils/file_parser.py`, add `parse_epub_structured(file_path) -> List[ChapterInfo]`:
   - Use ebooklib to read EPUB
   - Extract metadata: `book.get_metadata('DC', 'title')`, `book.get_metadata('DC', 'creator')`
   - Get spine order: `book.spine` → map item IDs to content
   - Parse TOC: `book.toc` → extract chapter titles and hrefs
   - For each TOC entry: find matching spine item → extract text via BeautifulSoup
   - Map to `ChapterInfo(num, title, content)`
   - Fallback: if TOC empty, split by spine items
2. Add `create_project_from_import(title, genre, chapters: List[ChapterInfo])` to ProjectManager
3. UI: file upload → show detected chapters preview (dataframe) → user confirms → create project
4. Add i18n keys

### Success Criteria
- [ ] EPUB with TOC → correctly parsed chapters with titles
- [ ] EPUB without TOC → chapters split by spine items
- [ ] Metadata (title, author) extracted
- [ ] Created project matches source chapter structure
- [ ] Handles EPUB2 and EPUB3

---

## Task 7: EPUB Export

### Requirements
- Export novel as EPUB 3.0 with metadata, TOC, CSS styling, chapter separation
- Use ebooklib (already in requirements.txt)

### Related Code Files
- **Modify:** `utils/exporter.py` — add `export_to_epub()`
- **Modify:** `ui/export_tab.py` — add EPUB option to format dropdown
- **Modify:** `locales/*/messages.json`

### Implementation Steps
1. In `utils/exporter.py`, add `export_to_epub(content, title, author="TiniX Story")`:
   - Create `epub.EpubBook()`, set metadata (title, language, identifier)
   - Parse chapters from content (reuse `_extract_chapters_from_markdown()`)
   - For each chapter: create `epub.EpubHtml`, set content with basic CSS
   - Add default CSS stylesheet for readable typography
   - Build TOC and spine
   - Write to temp file, return path
2. In `ui/export_tab.py`, add "EPUB" to format choices
3. Wire export button to call `export_to_epub()`

### Success Criteria
- [ ] Valid EPUB that opens in Calibre/Apple Books/Kindle
- [ ] TOC matches chapter structure
- [ ] Readable styling (fonts, margins, line spacing)
- [ ] Metadata populated

---

## Task 9: Project Archive Import/Export

### Requirements
- Export: ZIP with metadata JSON + chapters + settings
- Import: restore from ZIP
- Enables project sharing between instances

### Related Code Files
- **Create:** `utils/archive_manager.py` (~100 lines)
- **Modify:** `ui/projects_tab.py` — add archive buttons
- **Modify:** `locales/*/messages.json`

### Implementation Steps
1. Create `utils/archive_manager.py`:
   - `export_project_archive(project_id) -> str` (returns ZIP path):
     - Query project + chapters from DB
     - Write `metadata.json` (project data) + `chapters/` dir (one file per chapter)
     - Include `generation_cache` and `chapter_summaries` if exist
     - ZIP all → return temp file path
   - `import_project_archive(zip_path) -> tuple[bool, str]`:
     - Extract ZIP → read metadata.json
     - Create project via ProjectManager
     - Insert chapters, cache, summaries
     - Return success/error
2. UI: two buttons in Projects tab — "Export Archive" (per project), "Import Archive" (file upload)

### Success Criteria
- [ ] Export produces valid ZIP with all project data
- [ ] Import restores project identically
- [ ] Handles projects with 100+ chapters
- [ ] No data loss in round-trip (export → import)

---

## Task 8: PDF Export

### Requirements
- Professional typography with configurable settings
- Chapter title pages, TOC, page numbers

### Related Code Files
- **Modify:** `utils/exporter.py` — add `export_to_pdf()`
- **Modify:** `ui/export_tab.py` — add PDF option
- **Modify:** `requirements.txt` — add `reportlab` or `weasyprint`

### Implementation Steps
1. Add `weasyprint` to requirements.txt (better CSS support than reportlab)
2. In `utils/exporter.py`, add `export_to_pdf(content, title)`:
   - Generate HTML with professional CSS (reuse `export_to_html()` structure)
   - Add page-specific CSS: `@page { margin: 2cm; @bottom-center { content: counter(page); } }`
   - Add chapter break CSS: `h2 { page-break-before: always; }`
   - Convert HTML → PDF via weasyprint
3. Wire in export tab

### Success Criteria
- [ ] Clean, readable PDF with page numbers
- [ ] Chapter breaks on new pages
- [ ] Works with CJK characters (font support)

---

## Task 10: Bulk Import

### Requirements
- Upload multiple files → each becomes project, or merge as chapters
- Auto-detect chapter boundaries

### Related Code Files
- **Modify:** `ui/create_tab.py` — add bulk import section
- **Modify:** `utils/file_parser.py` — add batch parsing
- **Modify:** `locales/*/messages.json`

### Implementation Steps
1. In `ui/create_tab.py`, add "Bulk Import" accordion:
   - `gr.File(file_count="multiple")` for multi-file upload
   - Radio: "Each file = separate project" or "Merge into one project"
   - "Import" button → process files → show results
2. For separate mode: call existing `parse_novel_file()` per file, create project each
3. For merge mode: parse all files, concatenate, split into chapters, create single project

### Success Criteria
- [ ] Upload 5+ files at once
- [ ] Both modes work correctly
- [ ] Progress indicator during processing

---

## Risk Assessment
- **EPUB import**: edge cases with malformed EPUBs, DRM-protected files → catch exceptions, show user-friendly error
- **PDF export**: weasyprint has system dependencies (cairo, pango) → document in README, may need Docker support
- **Archive format**: ensure backward compatibility if schema changes → include version field in metadata.json

## Next Steps
After Phase 3: Phase 4 (UX Polish) — dashboard benefits from richer project data.
