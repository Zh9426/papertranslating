from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from docx import Document


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skill" / "scripts" / "validate_translation_docx.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
LOCAL_TMP_ROOT = Path(__file__).resolve().parent / ".tmp"


def build_docx(path: Path, paragraphs: list[tuple[str, str]]) -> None:
    doc = Document()
    for style_name, text in paragraphs:
        doc.add_paragraph(text, style=style_name)
    doc.save(path)


def run_validator(docx_path: Path, segments_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(docx_path), "--segments", str(segments_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


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


def test_fails_when_source_equation_numbers_are_missing_from_final_docx(local_tmp_dir: Path) -> None:
    docx_path = local_tmp_dir / "equation-gap.docx"
    build_docx(
        docx_path,
        [
            ("Title", "HDSP Translation"),
            ("Heading 1", "Methods"),
            ("Normal", "The deposition function is given in Eq. (1)."),
            ("Normal", "The hologram calculation continues in Eq. (8), Eq. (9), and Eq. (10)."),
        ],
    )

    result = run_validator(docx_path, FIXTURES / "source_segments_equation_gap.json")

    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert report["missing_equation_numbers"] == [2, 3, 4, 5, 6, 7]


def test_fails_when_translated_captions_drop_source_parameters(local_tmp_dir: Path) -> None:
    docx_path = local_tmp_dir / "caption-loss.docx"
    build_docx(
        docx_path,
        [
            ("Title", "HDSP Translation"),
            ("Caption", "Fig. 1. HDSP concept and printed objects. a: process schematic; b: target-zone detail."),
        ],
    )

    result = run_validator(docx_path, FIXTURES / "source_segments_caption_parameters.json")

    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert report["missing_caption_parameters"] == [
        {
            "caption_identifier": "fig-1",
            "missing_parameter_symbols": ["dc", "f0", "od", "p"],
        }
    ]


def test_fails_when_final_docx_drops_source_structural_markers(local_tmp_dir: Path) -> None:
    docx_path = local_tmp_dir / "marker-loss.docx"
    build_docx(
        docx_path,
        [
            ("Normal", "The deposition function is given in Eq. (1)."),
            ("Normal", "See Fig. 1 for the setup."),
        ],
    )

    result = run_validator(docx_path, FIXTURES / "source_segments_equation_gap.json")

    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert report["missing_structural_markers_from_docx"] == [
        {
            "marker_type": "equation_refs",
            "missing_values": ["eq.(10)", "eq.(5)", "eq.(6)", "eq.(7)", "eq.(8)", "eq.(9)"],
        }
    ]
