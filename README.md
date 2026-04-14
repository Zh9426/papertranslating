# Paper Translating Skill

`paper-translating` is a Codex skill for translating academic papers into structured Word deliverables while preserving layout-relevant structure, figures, formulas, references, and terminology consistency.

## What It Covers

- PDF, HTML, DOCX, or pasted-paper translation workflows
- domain-aware terminology selection
- structure-preserving source segmentation
- workbook-driven translation to reduce omissions and paragraph drift
- editable Word equation requirements
- internal cross-references for numbered bibliography citations
- final DOCX validation for figures, formulas, style separation, and fidelity

## Repository Layout

- `skill/SKILL.md`: main skill instructions
- `skill/references/`: translation discipline, termbase guidance, Word output contract
- `skill/scripts/`: extraction, segmentation, workbook, DOCX build, and validation scripts

## Install

Copy the `skill/` directory into your Codex skills directory and keep the folder name as `paper-translating`.

Typical personal installation path on this machine:

```text
C:\Users\Zh89\.codex\skills\paper-translating
```

## Core Workflow

1. Extract source structure from the paper.
2. Prepare ordered source segments.
3. Create a translation workbook.
4. Fill the workbook segment by segment.
5. Supply editable OMML for equation segments.
6. Validate workbook completeness and fidelity.
7. Build the final `.docx`.
8. Validate the final document before delivery.

## Hard Requirements

- Translation, not explanation
- Formal scientific Chinese register
- No silent omission of sections, formulas, captions, or application discussion
- Equations must be editable Word equations, not screenshots
- Numbered bibliography citations should resolve to internal reference targets

## Validation Scripts

- `skill/scripts/validate_translation_workbook.py`
- `skill/scripts/validate_translation_fidelity.py`
- `skill/scripts/validate_translation_docx.py`

Use these before considering any output deliverable complete.

## Update Policy

Every skill update must include:

1. code or documentation changes
2. a short update summary
3. a fuller update description

The repository tracks those in:

- `CHANGELOG.md`
- `RELEASE_NOTES.md`

Do not publish updates without synchronizing those two files.
