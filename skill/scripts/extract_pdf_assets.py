#!/usr/bin/env python3
"""Extract structured text and figure crops from a PDF into a manifest directory."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


CAPTION_RE = re.compile(
    r"^\s*(?P<kind>fig(?:ure)?|table|\u56fe|\u8868)\s*\.?\s*(?P<label>\d+[a-zA-Z]?)",
    re.IGNORECASE,
)


def load_fitz():
    try:
        import fitz  # type: ignore
    except ImportError as exc:  # pragma: no cover - dependency guidance
        raise SystemExit(
            "PyMuPDF is required. Install it with `python -m pip install pymupdf`."
        ) from exc
    return fitz


def block_text(block: dict) -> str:
    text_parts: list[str] = []
    for line in block.get("lines", []):
        line_parts: list[str] = []
        for span in line.get("spans", []):
            span_text = (span.get("text") or "").strip()
            if span_text:
                line_parts.append(span_text)
        if line_parts:
            text_parts.append(" ".join(line_parts))
    return "\n".join(text_parts).strip()


def rect_intersection_width(a: tuple[float, float, float, float], b: tuple[float, float]) -> float:
    return max(0.0, min(a[2], b[1]) - max(a[0], b[0]))


def classify_caption(text: str) -> dict[str, str] | None:
    first_line = text.splitlines()[0] if text else ""
    match = CAPTION_RE.match(first_line)
    if not match:
        return None
    kind = match.group("kind").lower()
    label = match.group("label")
    return {"kind": kind, "label": label}


def estimate_column_split(page_width: float, text_blocks: list[dict]) -> float | None:
    left = 0
    right = 0
    centers: list[float] = []
    for block in text_blocks:
        bbox = block["bbox"]
        width = bbox[2] - bbox[0]
        words = len(block["text"].split())
        if words < 8 or width < page_width * 0.22:
            continue
        center = (bbox[0] + bbox[2]) / 2
        centers.append(center)
        if center < page_width * 0.45:
            left += 1
        elif center > page_width * 0.55:
            right += 1
    if left >= 3 and right >= 3:
        return sum(centers) / len(centers)
    return None


def is_body_block(block: dict, region: tuple[float, float], page_width: float) -> bool:
    bbox = block["bbox"]
    width = bbox[2] - bbox[0]
    words = len(block["text"].split())
    if words < 8:
        return False
    if rect_intersection_width(bbox, region) < (width * 0.45):
        return False
    return width >= page_width * 0.2


def is_same_caption_row(current: dict, candidate: dict, page_height: float) -> bool:
    cy0, cy1 = current["bbox"][1], current["bbox"][3]
    ny0, ny1 = candidate["bbox"][1], candidate["bbox"][3]
    vertical_gap = max(0.0, max(cy0, ny0) - min(cy1, ny1))
    return vertical_gap <= max(8.0, page_height * 0.008)


def merge_caption_blocks(text_blocks: list[dict], page_height: float) -> list[dict]:
    merged: list[dict] = []
    consumed: set[int] = set()

    for index, block in enumerate(text_blocks):
        if index in consumed:
            continue

        caption_meta = classify_caption(block["text"])
        if not caption_meta:
            merged.append(block)
            continue

        parts = [block]
        consumed.add(index)
        left, top, right, bottom = block["bbox"]

        for next_index in range(index + 1, len(text_blocks)):
            candidate = text_blocks[next_index]
            if next_index in consumed:
                continue
            if not is_same_caption_row(block, candidate, page_height):
                if candidate["bbox"][1] > bottom + max(10.0, page_height * 0.012):
                    break
                continue
            parts.append(candidate)
            consumed.add(next_index)
            left = min(left, candidate["bbox"][0])
            top = min(top, candidate["bbox"][1])
            right = max(right, candidate["bbox"][2])
            bottom = max(bottom, candidate["bbox"][3])

        parts.sort(key=lambda item: item["bbox"][0])
        merged_text = " ".join(part["text"].replace("\n", " ").strip() for part in parts).strip()
        merged.append({"bbox": (left, top, right, bottom), "text": merged_text})

    merged.sort(key=lambda b: (b["bbox"][1], b["bbox"][0]))
    return merged


def region_for_caption(
    caption_block: dict, page_width: float, column_split: float | None
) -> tuple[float, float]:
    x0, _, x1, _ = caption_block["bbox"]
    caption_width = x1 - x0
    center = (x0 + x1) / 2
    if column_split is None or caption_width >= page_width * 0.58:
        return (page_width * 0.06, page_width * 0.94)
    if center <= column_split:
        return (page_width * 0.06, column_split - page_width * 0.02)
    return (column_split + page_width * 0.02, page_width * 0.94)


def find_crop_top(
    caption_block: dict,
    text_blocks: list[dict],
    region: tuple[float, float],
    page_height: float,
    page_width: float,
) -> float:
    caption_top = caption_block["bbox"][1]
    prior_body_bottoms: list[float] = []
    for block in text_blocks:
        if block is caption_block:
            continue
        if block["bbox"][3] > caption_top:
            continue
        if is_body_block(block, region, page_width):
            prior_body_bottoms.append(block["bbox"][3])

    top_margin = page_height * 0.08
    if not prior_body_bottoms:
        return top_margin

    crop_top = max(prior_body_bottoms) + 4
    max_allowed = max(top_margin, caption_top - page_height * 0.12)
    return min(crop_top, max_allowed)


def expand_region_with_image_blocks(
    caption_block: dict,
    image_blocks: list[tuple[float, float, float, float]],
    region: tuple[float, float],
    crop_top: float,
    page_width: float,
    page_height: float,
) -> tuple[float, float]:
    caption_top = caption_block["bbox"][1]
    related = []
    for bbox in image_blocks:
        if bbox[3] > caption_top:
            continue
        if bbox[1] < crop_top - max(20.0, page_height * 0.02):
            continue
        related.append(bbox)

    if not related:
        return region

    x0 = min(item[0] for item in related)
    x1 = max(item[2] for item in related)
    padding = max(18.0, page_width * 0.03)
    x0 = max(page_width * 0.04, x0 - padding)
    x1 = min(page_width * 0.96, x1 + padding)

    if (x1 - x0) >= page_width * 0.68:
        return (page_width * 0.06, page_width * 0.94)

    return (min(region[0], x0), max(region[1], x1))


def render_crop(page, fitz, clip_rect, output_path: Path, scale: float) -> None:
    matrix = fitz.Matrix(scale, scale)
    pixmap = page.get_pixmap(matrix=matrix, clip=clip_rect, alpha=False)
    pixmap.save(output_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", help="Input PDF file")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument(
        "--scale",
        type=float,
        default=2.6,
        help="Render scale used when cropping figures from the page image",
    )
    args = parser.parse_args()

    fitz = load_fitz()

    pdf_path = Path(args.pdf).expanduser().resolve()
    out_dir = Path(args.output_dir).expanduser().resolve()
    figures_dir = out_dir / "figures"
    embedded_dir = out_dir / "embedded_images"
    out_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    embedded_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    manifest: dict[str, object] = {
        "source_pdf": str(pdf_path),
        "page_count": doc.page_count,
        "pages": [],
    }

    for page_index in range(doc.page_count):
        page = doc.load_page(page_index)
        page_dict = page.get_text("dict")
        page_width = page.rect.width
        page_height = page.rect.height

        text_blocks: list[dict] = []
        image_blocks: list[tuple[float, float, float, float]] = []
        for block in page_dict.get("blocks", []):
            if block.get("type") == 1 and block.get("bbox"):
                image_blocks.append(tuple(block["bbox"]))
            if block.get("type") != 0:
                continue
            text = block_text(block)
            if not text:
                continue
            text_blocks.append({"bbox": block.get("bbox"), "text": text})

        text_blocks.sort(key=lambda b: (b["bbox"][1], b["bbox"][0]))
        text_blocks = merge_caption_blocks(text_blocks, page_height)
        column_split = estimate_column_split(page_width, text_blocks)

        captions: list[dict] = []
        figures: list[dict] = []
        for block in text_blocks:
            caption_meta = classify_caption(block["text"])
            if not caption_meta:
                continue
            region = region_for_caption(block, page_width, column_split)
            crop_top = find_crop_top(block, text_blocks, region, page_height, page_width)
            region = expand_region_with_image_blocks(
                block, image_blocks, region, crop_top, page_width, page_height
            )
            crop_bottom = max(crop_top + 12, block["bbox"][1] - 4)
            clip_rect = fitz.Rect(region[0], crop_top, region[1], crop_bottom)

            base_name = f"page-{page_index + 1:03d}-{caption_meta['kind']}-{caption_meta['label']}"
            output_path = figures_dir / f"{base_name}.png"
            render_crop(page, fitz, clip_rect, output_path, args.scale)

            figure_entry = {
                "kind": caption_meta["kind"],
                "label": caption_meta["label"],
                "caption": block["text"].replace("\n", " ").strip(),
                "path": str(output_path),
                "crop_bbox": [clip_rect.x0, clip_rect.y0, clip_rect.x1, clip_rect.y1],
                "caption_bbox": list(block["bbox"]),
                "column_region": list(region),
            }
            captions.append(figure_entry)
            if caption_meta["kind"] in {"fig", "figure", "\u56fe"}:
                figures.append(figure_entry)

        embedded_images = []
        for image_index, image_info in enumerate(page.get_images(full=True), start=1):
            xref = image_info[0]
            base_image = doc.extract_image(xref)
            extension = base_image.get("ext", "bin")
            image_path = embedded_dir / f"page-{page_index + 1:03d}-img-{image_index:02d}.{extension}"
            image_path.write_bytes(base_image["image"])
            embedded_images.append(
                {
                    "xref": xref,
                    "path": str(image_path),
                    "width": base_image.get("width"),
                    "height": base_image.get("height"),
                    "ext": extension,
                }
            )

        manifest["pages"].append(
            {
                "page_number": page_index + 1,
                "width": page_width,
                "height": page_height,
                "column_split": column_split,
                "text_blocks": text_blocks,
                "captions": captions,
                "figures": figures,
                "embedded_images": embedded_images,
            }
        )

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(manifest_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
