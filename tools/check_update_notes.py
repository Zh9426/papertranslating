from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REQUIRED_NOTE_FILES = {"CHANGELOG.md", "RELEASE_NOTES.md"}


def git_changed_files(base: str, head: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}..{head}"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def normalize(files: list[str]) -> set[str]:
    normalized = set()
    for file in files:
        normalized.add(Path(file).as_posix())
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Fail if files under skill/ changed without synchronized updates to "
            "CHANGELOG.md and RELEASE_NOTES.md."
        )
    )
    parser.add_argument("base", nargs="?")
    parser.add_argument("head", nargs="?")
    parser.add_argument(
        "--files",
        nargs="*",
        default=None,
        help="Explicit changed-file list. Use this instead of git revisions.",
    )
    args = parser.parse_args()

    if args.files is not None and (args.base or args.head):
        parser.error("Use either --files or <base> <head>, not both.")

    if args.files is not None:
        changed = normalize(args.files)
    elif args.base and args.head:
        changed = normalize(git_changed_files(args.base, args.head))
    else:
        parser.error("Provide --files or both <base> and <head> revisions.")

    skill_changed = any(path.startswith("skill/") for path in changed)
    notes_changed = REQUIRED_NOTE_FILES.issubset(changed)

    if skill_changed and not notes_changed:
        missing = ", ".join(sorted(REQUIRED_NOTE_FILES - changed))
        print(
            "Skill changes detected without synchronized update notes. "
            f"Missing: {missing}",
            file=sys.stderr,
        )
        return 2

    print("Update-note policy check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
