from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skill" / "scripts" / "extract_pdf_assets.py"


def load_module():
    spec = importlib.util.spec_from_file_location("extract_pdf_assets", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_merge_caption_blocks_merges_split_full_width_caption_row() -> None:
    module = load_module()
    text_blocks = [
        {
            "bbox": (306.1409912109375, 357.2213439941406, 561.2781982421875, 396.3235168457031),
            "text": "center) is constructed in low resolution by OD = 25 mm and high resolution by OD = 64 mm.",
        },
        {
            "bbox": (39.68498229980469, 358.70477294921875, 294.87310791015625, 406.2447204589844),
            "text": "Fig. 6 | Hologram-related process characterization of HDSP.",
        },
    ]

    merged = module.merge_caption_blocks(text_blocks, page_height=842.0)

    assert len(merged) == 1
    assert merged[0]["bbox"] == (
        39.68498229980469,
        357.2213439941406,
        561.2781982421875,
        406.2447204589844,
    )
    assert merged[0]["text"].startswith("Fig. 6 |")
