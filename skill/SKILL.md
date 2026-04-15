---
name: paper-translating
description: Translate academic papers from PDF, HTML, DOCX, or pasted text into a well-formatted Word document while preserving section structure, paragraph boundaries, figures, formulas, tables, citations, and terminology consistency. Use when the task is research literature translation, bilingual paper delivery, field-specific scientific terminology selection, or glossary-driven paper translation.
---

# PaperTranslating

## Overview

Use this skill to translate research papers into a `.docx` deliverable without flattening the source into plain text. Preserve title, authors, abstract, headings, paragraphs, figures, tables, captions, formulas, citations, appendices, and end matter.

This skill is for translation, not explanation or retelling. Keep the source paper's voice, paragraph structure, and logic flow unless the user explicitly asks for adaptation.
The default target register is formal scientific Chinese suitable for thesis and journal-style reading.

## Workflow

### 1. Lock the translation contract first

Before translating, confirm or assume the following:

- Source type: PDF, arXiv HTML, publisher page, DOCX, or pasted text
- Target language: default to Chinese unless the user specifies otherwise
- Output mode: Chinese only, bilingual paragraph alignment, or original plus translated appendix
- Terminology mode: user-specified domain first; otherwise infer from the paper
- Output artifact: final `.docx`
- Fidelity target: preserve figures, formulas, captions, references, section hierarchy, and paragraph boundaries

If the user gives no domain, infer it from title, abstract, keywords, arXiv category, journal section, or introduction text.

### 2. Prefer structure-preserving source acquisition

Choose the source in this order:

1. arXiv or publisher HTML when available and equations are readable
2. Native DOCX when available
3. PDF with page-level extraction
4. OCR only as a last resort

For PDF work:

- Extract page text blocks and image assets before translation
- Merge split caption fragments before deciding whether a figure is single-column or full-width
- Expand figure crops with both raster image bounds and vector drawing bounds so wide composite figures are not clipped to one column
- Prefer caption-anchored page-region crops over raw embedded-image export when reconstructing figures
- Preserve figure and table numbering and captions
- Keep formulas unchanged unless the formula contains natural-language labels that must be translated outside the equation body
- Do not silently drop side notes, appendices, acknowledgements, data-availability sections, code-availability sections, author-contribution sections, or conflict-of-interest statements

Use `scripts/extract_pdf_assets.py` to build a page manifest and export embedded images.

### 3. Select the terminology domain before bulk translation

Terminology selection order:

1. User-specified field or glossary
2. Journal or conference domain
3. arXiv or classification category
4. Automatic inference from the paper text

Run `scripts/detect_domain.py` on title, abstract, and introduction when the field is not explicit. Then consult [references/termbases.md](references/termbases.md) to choose one or two domain termbases.

Build a working glossary before translating dense sections:

- preferred Chinese term
- source English term
- allowed abbreviations
- terms that must remain untranslated
- ambiguous terms that need manual confirmation

When multiple domains overlap, bias toward the paper's contribution domain, not only the application domain.

### 4. Translation rules

Read [references/translation-discipline.md](references/translation-discipline.md) before translating narrative sections.

Translate faithfully and conservatively.

- Preserve section order exactly
- Preserve paragraph order exactly
- Preserve source paragraph boundaries by default: one source segment maps to one translated segment
- Preserve citation markers such as `[12]`, `(Smith et al., 2024)`, `Eq. (3)`, and `Fig. 2`
- Preserve variable names, symbols, units, dataset names, model names, algorithm names, and parameter ranges unless there is a stable standard Chinese rendering
- Preserve equation numbering, coefficient values, and displayed math blocks; do not jump from one equation number to another by omission
- Final equations must be editable Word equations backed by machine-readable math; equation images are not acceptable
- Preserve abstract detail, application-scope discussion, and figure-caption parameters; these are not optional compression targets
- Preserve threshold values, fitted coefficients, percentages, and other source-side numeric constants; these are mandatory reproducibility content
- Preserve a restrained academic register across the whole translation; avoid colloquial, tutorial, promotional, or oral-explanation phrasing
- Keep abbreviations consistent
- Do not rewrite claims, tone down uncertainty, strengthen conclusions, or turn the paper into commentary
- Do not replace the source voice with explanatory narration unless the source explicitly uses that perspective
- Do not merge, split, compress, summarize, or omit source paragraphs unless the source was only fragmented by PDF extraction and the join is explicitly justified in working notes
- Distinguish translation from explanation; explanations belong in notes, not in the main body unless the user asks

For difficult sentences, produce the best scientific Chinese first. If fidelity is uncertain, keep a short translator note outside the main translated paragraph or in a review log.

### 5. Prepare source segments before drafting translation

Run `scripts/prepare_translation_segments.py` on the extracted manifest before bulk translation.

Use the generated `source_id` values as the working translation skeleton:

- translate each `source_id` in order
- preserve `source_id` while drafting
- do not skip `source_id` entries without an explicit reason
- treat captions as captions and body segments as body paragraphs
- stop and regenerate or inspect segmentation if `validate_translation_fidelity.py` reports oversized source segments

This step exists to stop paragraph drift, accidental omission, and ad hoc restructuring.
It also provides the unit of checking for long-segment compression and missing critical constants.

### 6. Use a translation workbook, not free-form drafting

Run `scripts/create_translation_workbook.py` on the prepared source segments before translating.

Fill the workbook instead of writing free-form prose:

- every `source_id` must remain present
- every segment must receive `translated_text`
- every equation segment must also receive machine-readable `equation_omml`
- do not use `status = omitted` for deliverable builds; a complete translation must cover every `source_id`
- keep translator notes separate from `translated_text`

Run `scripts/validate_translation_workbook.py` before assembling the final document.

### 7. Handle figures, tables, and formulas explicitly

#### Figures and tables

- Extract and retain figure crops
- Keep each figure near its translated caption
- Keep table numbering and titles synchronized with the source
- If a table cannot be reconstructed cleanly, keep it as an image and translate the caption plus surrounding discussion

#### Formulas

- Use editable equations backed by machine-readable math
- If the source is PDF-only and equation conversion is unreliable, stop and obtain machine-readable math before final assembly; do not fall back to equation screenshots
- Never translate variable symbols
- Translate equation descriptions, assumptions, and symbol definitions faithfully
- Keep `Eq. (n)` references aligned between source and translation
- Do not deliver displayed formulas as plain body-text approximations or equation images

#### References and citations

- Preserve bibliography numbering
- Emit internal cross-references from in-text numeric citations to the corresponding bibliography entries whenever the citation format is numeric and resolvable
- Do not leave numbered bibliography citations as dead text if the output pipeline can resolve them to internal targets

#### Layout

- Preserve the reading structure, not pixel-perfect PDF geometry
- Favor a clean, editable Word document over a visually broken clone
- If the user supplies a Word template, use it
- If no template is supplied, use a clean research-report layout and keep figure and table placement stable
- Do not let figure captions, authors, metadata, equations, references, and body text collapse into the same paragraph style

### 8. Produce the Word deliverable

Final output must be `.docx`.

Preferred assembly order:

1. Build or reuse the glossary
2. Extract the source manifest
3. Prepare source segments
4. Create the translation workbook
5. Translate into the workbook while preserving `source_id`
6. Validate workbook completeness
7. Reinsert extracted images and captions
8. Reinsert equations or equation images
9. Assemble the final Word document
10. Review the rendered document page by page

Use `scripts/build_translation_docx.py` when you have structured JSON content to assemble. For formatting expectations, read [references/word-output.md](references/word-output.md).

Do not ship a final paper translation by generic markdown-to-docx conversion alone. The final deliverable should be emitted through a typed block structure and the controlled DOCX builder so captions, references, metadata, equations, and body text can use distinct styles.
The controlled DOCX builder should also preserve each `source_id` as a hidden bookmark so the final handoff can be checked for full source coverage.

### 9. Validation checklist

Before delivery, verify all of the following:

- title, authors, abstract, keywords, headings, paragraphs, and references are present
- no figure, table, appendix, acknowledgements section, or end matter was silently dropped
- captions still match figure and table numbering
- symbols, units, dataset names, and citations are intact
- terminology is consistent across the whole document
- the `.docx` opens cleanly and images render correctly
- the final output matches the requested mode
- figure count in the output is checked against the extracted source manifest
- caption paragraphs are not left in the default body style
- the final document is checked for mojibake or encoding-corrupted paragraphs
- the translation is checked for suspicious explanatory drift
- the translation is checked for register drift away from formal scientific prose
- the translated body paragraph count is compared against the prepared source segment count
- the translation workbook is checked for empty, missing, duplicate, or reordered `source_id` entries
- equation segments are checked for missing machine-readable `equation_omml`
- prepared source segments are checked for oversized multi-paragraph body chunks before translation starts
- the workbook is checked for suspicious sentence-count collapse that may indicate omission within a segment
- the workbook is checked for severe length collapse where a long source paragraph was reduced to a short summary sentence
- the workbook is checked for missing critical tokens such as percentages, thresholds, unit-bearing values, and fitted coefficient labels
- source figure, equation, and supplementary references are checked against the translation for structural marker loss
- caption parameter symbols such as `P`, `f0`, `DC`, and `OD` are checked against the translation
- the final document is checked for formula-style mismatches, plaintext equation paragraphs, and equation-image paragraphs
- the final document is checked for missing internal reference targets on numeric citations
- the final document is checked for missing `source_id` coverage against the prepared source segments

Run `scripts/validate_translation_docx.py` before handoff whenever a final `.docx` was produced.
When source segments exist, pass `--segments` to the DOCX validator so missing equation chains, caption parameters, source-derived structural markers, and missing `source_id` coverage can block release.
Run `scripts/validate_translation_fidelity.py` on the workbook before DOCX assembly, then on the final translation output before handoff.
Run `scripts/validate_translation_workbook.py` before DOCX assembly.
Treat any non-zero exit from the fidelity validator or DOCX validator as a release blocker.

## Resources

### scripts/

- `extract_pdf_assets.py`: export page manifests and figure crops from PDFs
- `detect_domain.py`: infer likely paper domain and recommend terminology sources
- `prepare_translation_segments.py`: prepare ordered source segments so translation can preserve paragraph boundaries
- `create_translation_workbook.py`: create a fill-in translation workbook that preserves every source segment
- `validate_translation_workbook.py`: verify no source segments were dropped, left empty, duplicated, or reordered
- `build_translation_docx.py`: assemble a translation deliverable from structured JSON and local images
- `validate_translation_docx.py`: verify figure count, caption styles, equation continuity, caption parameter preservation, structural markers, source-id coverage, and obvious encoding failures in the final DOCX
- `validate_translation_fidelity.py`: flag explanatory drift, register drift, oversized source segments, sentence-count collapse, and paragraph-count mismatch
- `validate_translation_fidelity.py`: also flags severe summary-style compression and missing critical numeric or coefficient tokens inside translated segments

### references/

- [references/termbases.md](references/termbases.md): domain-to-termbase mapping and selection rules
- [references/translation-discipline.md](references/translation-discipline.md): paragraph fidelity and anti-paraphrase rules
- [references/word-output.md](references/word-output.md): Word output contract and formatting rules
