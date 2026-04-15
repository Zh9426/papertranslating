# Translation Validation Hardening Design

Date: 2026-04-15
Repository: `F:\GitHub\papertranslating`
Status: Draft for review

## Context

The current `paper-translating` repository already extracts substantially more source structure than a bad final translation may preserve. In the reviewed HDSP sample, the repository extraction pipeline recovered:

- equation segments for `Eq. (2)` through `Eq. (15)`
- coefficient values attached to `Eq. (1)`
- figure-caption parameter symbols such as `OD`, `P`, `f0`, and `DC`
- body paragraphs covering biomedical applications, porosity thresholds, and other discussion details

However, the reviewed translated `.docx` still passed `skill/scripts/validate_translation_docx.py` even though it had severe fidelity defects:

- `Eq. (2)` through `Eq. (7)` were missing from the final document
- the final document used equation labels without validating that the equations themselves existed
- figure captions omitted key experimental parameters
- major body paragraphs were omitted, producing a much shorter "compressed version" rather than a full translation

`skill/scripts/validate_translation_fidelity.py --segments` detected a large body-paragraph deficit for the same sample, but that validation is not sufficient on its own to guarantee that a final `.docx` preserves formula chains, caption parameters, and required structural markers.

## Problem Statement

The repository currently allows a structurally incomplete paper translation to survive the final validation stage. This creates a false sense of completion and undermines the repository's core contract: the output must be a faithful, full-paper translation rather than a shortened paraphrase.

## Goals

- Block final `.docx` delivery when equation numbering is discontinuous or when source equations are missing from the final output.
- Block final `.docx` delivery when figure-caption parameter symbols present in the source are absent from translated captions.
- Block final `.docx` delivery when key structural markers from the source are lost in translation output.
- Make the final validation workflow explicitly depend on both fidelity validation and docx-specific validation.
- Add regression coverage based on the HDSP sample failure mode so the gap cannot silently reappear.

## Non-Goals

- Fully automating PDF-to-OMML equation reconstruction from arbitrary source PDFs.
- Rebuilding the entire translation workflow or replacing the workbook model.
- Introducing a new external service or remote dependency.
- Solving all OCR-quality problems in one change.

## Design Summary

The implementation will harden the repository at three layers:

1. Final DOCX validation will become structure-aware instead of only style-aware.
2. Validation flow requirements will explicitly require source-segment-backed fidelity checks before final delivery.
3. The repository will gain a regression fixture and tests derived from the reviewed HDSP failure case.

The immediate priority is to stop invalid final `.docx` outputs from being treated as acceptable. Extraction improvements remain secondary because the reviewed sample shows that the source pipeline already captures most of the missing information.

## Proposed Changes

## 1. Strengthen final DOCX validation

File target:

- `skill/scripts/validate_translation_docx.py`

Add final-output checks that compare the translated `.docx` against source-derived expectations.

### 1.1 Equation continuity checks

When source segments are available, the validator should:

- detect all source equation numbers referenced in source segments
- detect all equation numbers referenced in the final document
- report missing equation references that indicate numbering jumps such as source containing `2..7` while final output jumps from `1` to `8`
- distinguish between:
  - missing equation references
  - missing equation bodies
  - equation-style paragraphs that contain no OMML

This check is needed because the current validator only flags plaintext equations when they are already styled as `PaperEquation`. It does not fail a document that silently omits equations entirely.

### 1.2 Caption parameter preservation checks

When source segments are available, the validator should:

- extract parameter symbols from source caption segments, such as `P`, `f0`, `DC`, `OD`, `SNR`, and similar notation already used by the fidelity validator
- locate translated caption paragraphs in the final `.docx`
- compare per-caption or aggregate caption parameter coverage
- fail if source caption parameters disappear from translated captions without justification

This directly addresses the HDSP sample where the final document kept figure captions but stripped the experimental parameters required for reproducibility.

### 1.3 Structural marker preservation checks in final DOCX

Extend final-output checking so that the translated `.docx` is also compared against source structural markers:

- figure references
- equation references
- supplementary figure/table/movie references
- selected parameter symbols in captions

The repository already computes similar signals in `validate_translation_fidelity.py` for workbook JSON. The hardening work should reuse or align with that logic rather than inventing a second incompatible rule set.

## 2. Tighten validation flow expectations

File targets:

- `skill/SKILL.md`
- `README.md`
- `CONTRIBUTING.md`

Make the repository contract explicit:

- final delivery is blocked unless `validate_translation_workbook.py`, `validate_translation_fidelity.py`, and `validate_translation_docx.py` all pass
- when validating a final `.docx`, source segments should be supplied whenever they exist
- failing fidelity validation is a release blocker even if DOCX formatting checks pass

This change is partly documentation, but it matters because the current tooling split makes it too easy to run the DOCX validator in isolation and believe the document is ready.

## 3. Add regression-focused tests

File targets:

- new tests under `tests/` or repository-equivalent validation test location
- possibly small helper modules if script logic must be extracted for testability

Add tests that reproduce the identified failure mode with minimal fixtures.

### 3.1 Equation-gap regression

Create a fixture representing:

- source expectations containing `Eq. (1)` through `Eq. (10)`
- final document text containing equation references that jump from `Eq. (1)` to `Eq. (8)`

Expected result:

- final docx validator fails with a clear report listing missing equation numbers or missing equation bodies

### 3.2 Caption-parameter regression

Create a fixture representing:

- source caption text containing `OD`, `P`, `f0`, and `DC`
- translated caption text that omits them

Expected result:

- validator fails and reports missing caption parameters

### 3.3 Full-sample regression hooks

Do not commit the user's original paper files into the repository. Instead:

- create minimal sanitized fixtures inspired by the HDSP sample
- encode the same failure class without carrying external paper assets into version control

This keeps the repository lightweight while preserving the bug's behavioral signature.

## Data Flow

Expected hardened validation flow:

1. `extract_pdf_assets.py` produces `manifest.json`
2. `prepare_translation_segments.py` produces ordered source segments
3. translation workbook is created and filled
4. `validate_translation_workbook.py` confirms completeness
5. `validate_translation_fidelity.py --segments` confirms source-to-translation fidelity
6. final `.docx` is assembled
7. `validate_translation_docx.py` runs with source-derived expectations and blocks release on structural loss

## Error Reporting

Validation reports should remain JSON and add explicit machine-readable fields for:

- `missing_equation_numbers`
- `missing_equation_bodies`
- `missing_caption_parameters`
- `missing_structural_markers_from_docx`

The reports should stay human-readable enough for manual debugging and precise enough for future CI integration.

## Testing Strategy

- Write failing tests first for equation-gap and caption-parameter loss.
- Confirm the current validator behavior fails to catch the regression before changing implementation.
- Implement the smallest validator changes necessary to make the tests pass.
- Re-run the existing script compile check and targeted validation tests.

## Risks

- Equation-number extraction may be noisy when the source PDF is badly fragmented.
- Some papers use equation references inconsistently, so checks must tolerate documents with no numbered equations.
- Aggregate caption comparison can produce false positives if parameters are intentionally moved out of captions; this should be documented and tuned conservatively.

## Mitigations

- Only enforce equation continuity when numbered equations are clearly present in the source.
- Restrict caption-parameter checks to symbols explicitly found in source caption segments.
- Prefer deterministic source-segment comparisons over heuristic full-document guesses.

## Open Decisions

- Whether the final DOCX validator should accept either source `segments.json` or `manifest.json`, or require segments when equation/caption comparisons are requested.
- Whether shared marker-extraction logic should be factored into a common helper module now or left duplicated for a smaller first patch.

## Recommended First Implementation Slice

Implement the smallest slice that materially closes the gap:

1. add failing tests for equation-number gaps and caption-parameter loss
2. extend `validate_translation_docx.py` to accept source segments and report those failures
3. update skill and repository docs so the full validation sequence is mandatory

This sequence provides an immediate safety win without expanding scope into full equation reconstruction.
