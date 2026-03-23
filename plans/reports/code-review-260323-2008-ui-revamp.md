# Code Review: UI Revamp (CSS Enhancement)

**Date:** 2026-03-23 | **Score: 8/10** | **Focus:** CSS theming, dashboard cards, novel-text styling

---

## Scope

| Item | Detail |
|------|--------|
| Files reviewed | `custom.css` (663 LOC), `ui/projects_tab.py` (639 LOC), `ui/continue_tab.py` (partial) |
| Change type | CSS-only theme + minor Python elem_classes additions |
| Risk level | Low — presentational changes, no business logic altered |

## Overall Assessment

Well-structured CSS revamp. Good use of design tokens (CSS custom properties), consistent naming, sensible responsive breakpoints, and clean separation of concerns. The novel-text book-like styling is appropriate for a reading/writing app. A few issues worth addressing below.

---

## Critical Issues

### 1. XSS in Dashboard HTML (projects_tab.py, lines 17-38)

`_build_dashboard_html()` interpolates DB-sourced values (`title`, `genre`, `updated_at`) directly into raw HTML without escaping.

```python
cards_html += f"""
<div class='project-card-title'>{title}</div>
<span class='project-card-genre'>{genre}</span>
```

If a user creates a project with title `<img src=x onerror=alert(1)>`, it executes in the browser.

**Fix:** Import `html.escape` and wrap all user-sourced values:
```python
import html
title = html.escape(p.get("title", ""))
genre = html.escape(p.get("genre", ""))
```

**Severity:** Critical (stored XSS)

---

## High Priority

### 2. External font dependency without fallback verification

Line 3 of `custom.css` loads 4 Google Fonts families via `@import url(...)`. This is a blocking request — if Google Fonts is unreachable (air-gapped environments, China, slow connections), font loading delays page render.

**Recommendation:**
- Add `font-display: swap` (already in the URL via `&display=swap` -- good)
- Consider self-hosting fonts or using `<link rel="preconnect">` in the app header for faster loads
- Fallback chains look adequate (`Georgia`, `system-ui`)

**Severity:** Medium-High (availability concern, not a bug)

### 3. CSS loaded via `gr.HTML` injection instead of Gradio's `css` param

In `app.py:65`:
```python
gr.HTML(f"<style>{custom_css}</style>", visible=False)
```

Gradio's `gr.Blocks(css=custom_css)` param is the idiomatic way and avoids a hidden HTML element. The current approach works but may cause FOUC (flash of unstyled content) since the style element is rendered as a component rather than in `<head>`.

**Fix:**
```python
with gr.Blocks(title=t("app.title"), css=custom_css) as app:
```

---

## Medium Priority

### 4. Excessive `!important` usage (50+ instances)

Nearly every CSS rule uses `!important`. While necessary to override Gradio's inline styles, it creates a maintenance burden — future overrides require more specificity hacks.

**Recommendation:** Accept as pragmatic for Gradio theming. Document in code comment that `!important` is required to override Gradio defaults.

### 5. `novel-text` class applied inconsistently

Only 3 textboxes get `novel-text`: editor (projects_tab), content display (continue_tab), tool output (text_tools). The create tab's output and rewrite/polish outputs do not have it.

**Recommendation:** Audit all content-display textboxes and apply `novel-text` consistently where chapter/novel content is shown.

### 6. Dashboard grid min-width hardcoded

Line 40: `grid-template-columns:repeat(auto-fill,minmax(320px,1fr))` — on very narrow screens (<320px), cards overflow.

**Minor** — the responsive breakpoint at 768px helps, but consider `minmax(280px,1fr)` for better small-screen support.

---

## Low Priority

### 7. Orphaned CSS classes

`dashboard-table`, `dashboard-header` classes (lines 399-433) appear to be from the old table-based dashboard. Grep confirms no Python code generates these classes anymore. Dead CSS.

**Recommendation:** Remove orphaned table-related CSS to reduce file size.

### 8. Magic numbers in CSS

Some values like `120px`, `60px`, `8px` dot sizes appear without design token references. Minor consistency issue.

---

## Positive Observations

- **Design tokens** — Clean variable system in `:root` with semantic naming
- **Transition system** — Three-tier transition speeds (fast/base/slow) applied consistently
- **Responsive design** — Mobile breakpoint handles tab wrapping and card layout gracefully
- **Animations** — Subtle shimmer loading and pulse-dot are tasteful, not distracting
- **Card-based dashboard** — Much better UX than previous table layout; progress bars with gradient fill look polished
- **Error handling** — `_build_dashboard_html` handles empty stats gracefully
- **Novel-text styling** — `line-height: 2`, serif font, subtle background gradient create genuine book-like feel

---

## Recommended Actions (Prioritized)

1. **[Critical]** Add `html.escape()` to all user-sourced values in `_build_dashboard_html()`
2. **[High]** Move CSS to `gr.Blocks(css=...)` param instead of `gr.HTML` injection
3. **[Medium]** Apply `novel-text` class to all novel content textboxes consistently
4. **[Low]** Remove orphaned dashboard-table CSS classes

## Metrics

| Metric | Value |
|--------|-------|
| CSS LOC | 663 |
| Design tokens | 30+ |
| `!important` count | ~55 |
| Responsive breakpoints | 1 (768px) |
| Animations | 2 (shimmer, pulse-dot) |
| XSS vectors found | 1 (dashboard HTML) |

## Unresolved Questions

- Is the app expected to run in air-gapped/offline environments? If so, Google Fonts dependency needs self-hosting.
- Should `novel-text` styling also apply to the create tab's generated output display?
