# Contributing

## Scope

This repository is for the `paper-translating` Codex skill only.

## Required Update Procedure

Whenever you change the skill:

1. update files under `skill/`
2. run `python -m pytest tests/test_validate_translation_docx.py -q`
3. run the relevant validation scripts
4. run `python tools/check_update_notes.py --files <changed files>` as a quick gate
5. update `CHANGELOG.md`
6. update `RELEASE_NOTES.md`
7. commit all of the above together

## Release Expectations

- keep equations editable
- keep numeric bibliography cross-references live
- keep translation output in formal scientific Chinese
- do not weaken validation gates without documenting why
- do not merge `skill/` changes unless `CHANGELOG.md` and `RELEASE_NOTES.md` changed in the same diff
