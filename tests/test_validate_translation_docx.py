from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path
from zipfile import ZipFile

import pytest
from docx import Document


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skill" / "scripts" / "validate_translation_docx.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
LOCAL_TMP_ROOT = Path(__file__).resolve().parent / ".tmp"
BUILD_SCRIPT = REPO_ROOT / "skill" / "scripts" / "build_translation_docx.py"


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


def run_builder(payload_path: Path, output_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(BUILD_SCRIPT), str(payload_path), str(output_path)],
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


def test_fails_when_final_docx_lacks_source_id_coverage(local_tmp_dir: Path) -> None:
    docx_path = local_tmp_dir / "source-id-gap.docx"
    build_docx(
        docx_path,
        [
            ("Normal", "Only one visible paragraph made it into the final document."),
        ],
    )

    result = run_validator(docx_path, FIXTURES / "source_segments_source_id_coverage.json")

    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert report["missing_source_ids_from_docx"] == ["S0001", "S0002", "S0003"]


def test_builder_embeds_source_id_bookmarks_into_final_docx(local_tmp_dir: Path) -> None:
    payload_path = local_tmp_dir / "payload.json"
    docx_path = local_tmp_dir / "built.docx"
    payload_path.write_text(
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
                        "type": "equation",
                        "translated_text": "公式（8）",
                        "equation_omml": (
                            '<m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
                            'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                            "<m:oMath><m:r><m:t>x=1</m:t></m:r></m:oMath></m:oMathPara>"
                        ),
                        "status": "translated",
                    },
                    {
                        "source_id": "S0003",
                        "type": "caption",
                        "translated_text": "Fig. 1. 完整图注。",
                        "equation_omml": None,
                        "status": "translated",
                    },
                ]
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    build_result = run_builder(payload_path, docx_path)

    assert build_result.returncode == 0, build_result.stderr or build_result.stdout
    with ZipFile(docx_path) as archive:
        document_xml = archive.read("word/document.xml").decode("utf-8")
    assert 'w:name="seg-s0001"' in document_xml
    assert 'w:name="seg-s0002"' in document_xml
    assert 'w:name="seg-s0003"' in document_xml


def test_fails_when_formula_text_is_left_in_body_paragraphs(local_tmp_dir: Path) -> None:
    docx_path = local_tmp_dir / "plaintext-formula.docx"
    build_docx(
        docx_path,
        [
            ("Normal", "Correlation = ΣΣ(Ri,j - R̄)(Ai,j - Ā) / sqrt(...)"),
        ],
    )

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(docx_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert report["formula_style_mismatches"] == [
        "Correlation = ΣΣ(Ri,j - R̄)(Ai,j - Ā) / sqrt(...)"
    ]
