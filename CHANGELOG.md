# Changelog

All notable updates to `paper-translating` should be recorded here.

## Unreleased

### Summary

- Packaged the skill for public distribution and added repository-level enforcement for update summaries and descriptions.
- Hardened final DOCX validation so source-derived equation gaps, caption parameter loss, and structural marker loss now fail before delivery.

### Description

- Added the standalone public repository layout for `paper-translating`, including installation and usage guidance, and introduced an explicit update-notes gate so future `skill/` changes must be accompanied by synchronized `CHANGELOG.md` and `RELEASE_NOTES.md` updates.
- Added regression tests and stricter final document checks that compare translated DOCX output against prepared source segments, catching missing numbered equations, stripped caption parameters, and dropped source structural markers that previously escaped the final validation stage.
