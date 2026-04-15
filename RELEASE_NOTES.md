# Release Notes

## Latest Update

### Summary

Initial public release of the `paper-translating` skill repository, with enforced update-note synchronization for future skill changes.
Hardened final DOCX validation so source-derived equation gaps, caption parameter loss, and structural marker loss now fail before delivery.

### Description

This release packages the local Codex skill into a standalone repository with installation guidance, validation scripts, strict translation-fidelity rules, editable Word equation requirements, numeric-reference cross-link support, and a repository-level guard that requires matching changelog and release-note updates whenever the packaged skill changes.
The validation pipeline now also compares translated DOCX output against prepared source segments, adding regression-tested checks for missing numbered equations, stripped caption parameters, and dropped structural markers that a formatting-only final pass would previously miss.

## Update Rule

For every future update:

1. update the Summary section with a short one-paragraph change overview
2. update the Description section with a fuller explanation of what changed and why
3. commit those note changes in the same commit as the skill update
