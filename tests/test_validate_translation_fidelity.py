from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skill" / "scripts" / "validate_translation_fidelity.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
LOCAL_TMP_ROOT = Path(__file__).resolve().parent / ".tmp"


@pytest.fixture
def local_tmp_dir() -> Path:
    path = LOCAL_TMP_ROOT / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        for item in sorted(path.rglob("*"), reverse=True):
            if item.is_file():
                item.unlink()
            else:
                item.rmdir()
        path.rmdir()


def run_validator(payload_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(payload_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_fails_when_long_body_segment_is_collapsed_to_a_short_summary() -> None:
    result = run_validator(FIXTURES / "workbook_critical_content_drop.json")

    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert report["suspicious_length_drop"] == [
        {
            "page_number": 12,
            "source_id": "S0101",
            "source_word_count": 60,
            "target_character_count": 14
        }
    ]


def test_fails_when_critical_numeric_tokens_disappear_from_translation() -> None:
    result = run_validator(FIXTURES / "workbook_numeric_token_drop.json")

    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert report["missing_critical_tokens"] == [
        {
            "missing_tokens": ["1%", "1.24", "100%", "10^2", "10^3", "14%", "2", "2.18", "2.88", "50%", "a0", "a01", "a10", "mpa"],
            "page_number": 8,
            "source_id": "S0102"
        }
    ]
