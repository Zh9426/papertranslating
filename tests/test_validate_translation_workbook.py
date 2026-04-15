from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skill" / "scripts" / "validate_translation_workbook.py"
BUILD_SCRIPT = REPO_ROOT / "skill" / "scripts" / "build_translation_docx.py"
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


def test_workbook_validator_rejects_omitted_segments(local_tmp_dir: Path) -> None:
    workbook_path = local_tmp_dir / "workbook.json"
    workbook_path.write_text(
        json.dumps(
            {
                "segments": [
                    {
                        "source_id": "S0001",
                        "type": "body",
                        "translated_text": "第一段落。",
                        "equation_omml": None,
                        "status": "translated",
                    },
                    {
                        "source_id": "S0002",
                        "type": "body",
                        "translated_text": "",
                        "equation_omml": None,
                        "status": "omitted",
                    },
                ]
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(workbook_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert report["omitted_segment_ids"] == ["S0002"]


def test_builder_refuses_workbooks_with_omitted_segments(local_tmp_dir: Path) -> None:
    workbook_path = local_tmp_dir / "workbook.json"
    output_path = local_tmp_dir / "output.docx"
    workbook_path.write_text(
        json.dumps(
            {
                "segments": [
                    {
                        "source_id": "S0001",
                        "type": "body",
                        "translated_text": "第一段落。",
                        "equation_omml": None,
                        "status": "translated",
                    },
                    {
                        "source_id": "S0002",
                        "type": "body",
                        "translated_text": "",
                        "equation_omml": None,
                        "status": "omitted",
                    },
                ]
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(BUILD_SCRIPT), str(workbook_path), str(output_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert result.returncode != 0
    assert "omitted segments are not permitted" in (result.stderr + result.stdout)
