# Word Output Contract

The final deliverable is an editable `.docx`, not a plain text dump.

## Default structure

1. Title
2. Authors and affiliations if present in the source
3. Abstract
4. Keywords if present
5. Main sections and subsections
6. Figures, tables, equations, captions, and appendices
7. References

## Output modes

### Chinese only

- Best when the user wants a clean translated deliverable
- Keep original citations and numbering

### Bilingual aligned

- Use when the user wants side-by-side or paragraph-pair verification
- Preferred layout: original paragraph followed by translated paragraph
- Mark translated paragraphs consistently

## Formatting rules

- Preserve heading hierarchy
- Keep figure and table numbers unchanged unless the user asks for renumbering
- Keep captions adjacent to their figure/table
- Keep displayed equations centered and readable
- Preserve equation numbering, coefficient values, and symbol definitions exactly
- Do not delete experimental parameters from captions, legends, or inline result descriptions
- Equations must remain editable in Word; equation screenshots or image-only formulas are not acceptable final output
- Reference citations should be emitted as internal cross-references to the corresponding bibliography entries whenever the numbering format allows it
- Do not force tables into broken editable grids if image form is more faithful
- Preserve bullet lists, numbered lists, and appendix labels
- Do not leave body paragraphs, captions, references, and metadata in the same default paragraph style

## Default typography

- Title: centered, bold, larger than body text
- Authors: centered, smaller than title
- Affiliations and DOI: centered metadata style
- Body text: Songti or equivalent East Asian serif, 12 pt, first-line indent, 1.5 line spacing
- Figure and table captions: centered, one size smaller than body text, visually distinct from body text
- References: hanging indent and smaller than or equal to body text
- Translator notes: visually separated from the main text

## Images and formulas

- Extract images to a stable folder and insert from local paths
- For equations, use editable Word equations backed by machine-readable math
- Do not replace displayed equations with screenshots or rendered images in the final submission
- Do not flatten display equations into plain text when Word equation objects are required for readability
- Preserve `Eq. (n)` references in translated prose whenever they appear in the source

## Review checklist

- `.docx` opens without repair prompts
- No missing images
- No duplicate captions
- No corrupted symbols or Greek letters
- No lost references or appendix labels
- No missing equation blocks or skipped equation numbers that were present in the source
- No figure-caption parameter loss for items such as `P`, `f0`, `DC`, or `OD`
- Equation paragraphs use editable math objects rather than images
- In-text bibliography citations resolve to internal reference targets where the numbering scheme permits cross-reference generation
- Terminology is consistent from title through references discussion
- Figure-caption count in the document matches the figures detected during extraction
- Caption paragraphs do not use the same paragraph style as the main body
- No obvious mojibake in the final Chinese output
