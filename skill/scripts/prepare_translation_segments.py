#!/usr/bin/env python3
"""Prepare ordered source segments from a PDF extraction manifest for faithful translation."""

from __future__ import annotations

import argparse
import json
import re
import statistics
from pathlib import Path


HEADER_PATTERNS = (
    re.compile(r"^Article\s+https?://doi\.org/", re.IGNORECASE),
    re.compile(r"^Nature Communications\s+\|", re.IGNORECASE),
)

HEADING_PATTERNS = (
    re.compile(r"^(abstract|introduction|results|discussion|methods|references)$", re.IGNORECASE),
    re.compile(
        r"^(data availability|code availability|acknowledg(e)?ments|author contributions|competing interests|supplementary information)$",
        re.IGNORECASE,
    ),
)

PARAGRAPH_START_PATTERNS = (
    re.compile(
        r"^(however|moreover|furthermore|additionally|later|recently|similar to|to remedy|in order to|here|we |this |these |the |for |beyond|overall|finally|notably|another |on the other hand)",
        re.IGNORECASE,
    ),
    re.compile(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b"),
)

TERMINAL_PUNCTUATION_RE = re.compile(r"[.!?。！？][\"')\]]*$")
METADATA_PATTERNS = (
    re.compile(r"^(received|accepted|published online|check for updates)\b", re.IGNORECASE),
    re.compile(r"^e-?mail:", re.IGNORECASE),
    re.compile(r"^https?://doi\.org/", re.IGNORECASE),
)
EQUATION_SYMBOL_RE = re.compile(
    r"(?:\b(?:NMSE|PSNR|SNR|Correlation|VDR)\b|[=∑Σϕφψλμωαβγδρτ]|\|\||\^|_2|\bk\s*[xy]\b|\bp\s*\()"
)

CONTINUATION_END_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "where",
    "which",
    "with",
}

CONTINUATION_START_WORDS = {
    "a",
    "an",
    "and",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "via",
    "where",
    "which",
    "with",
}


def normalize_space(text: str) -> str:
    return " ".join(text.split())


def normalize_pdf_text(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = re.sub(r"(?<=[A-Za-z])-\n(?=[a-z])", "", text)
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n\s+", "\n", text)
    return text.strip()


def is_header_or_footer(text: str) -> bool:
    stripped = normalize_space(text)
    if not stripped:
        return True
    if any(pattern.search(stripped) for pattern in HEADER_PATTERNS):
        return True
    if re.fullmatch(r"\d+", stripped):
        return True
    return False


def is_explicit_heading(text: str) -> bool:
    stripped = normalize_space(text).rstrip(".").strip()
    if any(pattern.fullmatch(stripped) for pattern in HEADING_PATTERNS):
        return True
    if "," in stripped or len(stripped.split()) > 5:
        return False

    words = [word for word in re.findall(r"[A-Za-z][A-Za-z/-]*", stripped) if word]
    if not words:
        return False
    titlecase_like = sum(1 for word in words if word[0].isupper())
    return titlecase_like >= max(1, len(words) - 1)


def is_equation_like(text: str) -> bool:
    stripped = normalize_space(text)
    if len(stripped) < 6 or len(stripped) > 240:
        return False
    if stripped.lower().startswith(("fig.", "figure ", "table ", "supplementary ")):
        return False

    signals = 0
    if "=" in stripped:
        signals += 1
    if EQUATION_SYMBOL_RE.search(stripped):
        signals += 1
    if re.search(r"\b[a-zA-Z]\s*=\s*[-+0-9(]", stripped):
        signals += 1
    if re.search(r"\b(?:Eq\.?\s*\(?\d+\)?|[A-Za-z]+\([A-Za-z0-9,\s]+\)\s*=)", stripped):
        signals += 1

    token_count = len(re.findall(r"[A-Za-z0-9]+", stripped))
    return signals >= 2 and token_count <= 70


def classify_segment_type(text: str) -> str:
    stripped = normalize_space(text)
    if is_explicit_heading(stripped):
        return "heading"
    if any(pattern.search(stripped) for pattern in METADATA_PATTERNS) or "@" in stripped:
        return "metadata"
    if re.fullmatch(r"(fig(?:ure)?|table|图|表)\s*\.?\s*\d+[a-zA-Z]?", stripped, re.IGNORECASE):
        return "caption"
    if is_equation_like(stripped):
        return "equation"
    return "body"


def block_width(block: dict) -> float:
    bbox = block.get("bbox") or [0, 0, 0, 0]
    return float(bbox[2] - bbox[0])


def block_center_x(block: dict) -> float:
    bbox = block.get("bbox") or [0, 0, 0, 0]
    return float((bbox[0] + bbox[2]) / 2)


def order_page_blocks(text_blocks: list[dict], page_width: float, column_split: float | None) -> list[dict]:
    if column_split is None:
        return sorted(text_blocks, key=lambda block: (block["bbox"][1], block["bbox"][0]))

    full_width_blocks = []
    left_column = []
    right_column = []

    for block in text_blocks:
        bbox = block["bbox"]
        width = block_width(block)
        if width >= page_width * 0.62 or (bbox[0] < column_split < bbox[2]):
            full_width_blocks.append(block)
        elif block_center_x(block) <= column_split:
            left_column.append(block)
        else:
            right_column.append(block)

    full_width_blocks.sort(key=lambda block: (block["bbox"][1], block["bbox"][0]))
    left_column.sort(key=lambda block: (block["bbox"][1], block["bbox"][0]))
    right_column.sort(key=lambda block: (block["bbox"][1], block["bbox"][0]))

    if not left_column and not right_column:
        return full_width_blocks

    first_column_top = min(
        [block["bbox"][1] for block in left_column + right_column],
        default=0.0,
    )

    ordered: list[dict] = []
    deferred_full_width = []
    for block in full_width_blocks:
        if block["bbox"][1] <= first_column_top:
            ordered.append(block)
        else:
            deferred_full_width.append(block)

    ordered.extend(left_column)
    ordered.extend(right_column)
    ordered.extend(deferred_full_width)
    return ordered


def should_start_new_paragraph(current_lines: list[str], next_line: str, median_line_length: float) -> bool:
    previous_line = current_lines[-1].rstrip()
    current_text = " ".join(current_lines).strip()
    if not previous_line or not current_text:
        return False
    if not TERMINAL_PUNCTUATION_RE.search(previous_line):
        return False

    strong_starter = any(pattern.match(next_line) for pattern in PARAGRAPH_START_PATTERNS)
    previous_length = len(previous_line)

    if strong_starter and previous_length <= median_line_length * 0.90:
        return True
    if strong_starter and len(current_text) >= 420:
        return True
    if re.match(r"^[A-Z][a-z]", next_line) and previous_length <= median_line_length * 0.75:
        return True
    if re.match(r"^[A-Z][a-z]", next_line) and len(current_text) >= 520:
        return True
    return False


def split_body_text_into_paragraphs(text: str) -> list[str]:
    text = normalize_pdf_text(text)
    lines = [" ".join(line.split()) for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    if len(lines) == 1:
        return [normalize_space(lines[0])]

    line_lengths = [len(line) for line in lines]
    median_line_length = statistics.median(line_lengths)

    paragraphs: list[str] = []
    current_lines = [lines[0]]

    for line in lines[1:]:
        if should_start_new_paragraph(current_lines, line, median_line_length):
            paragraphs.append(normalize_space(" ".join(current_lines)))
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        paragraphs.append(normalize_space(" ".join(current_lines)))

    return [paragraph for paragraph in paragraphs if paragraph]


def split_text_block(block: dict) -> list[dict]:
    text = block.get("text", "").strip()
    if is_header_or_footer(text):
        return []

    segment_type = classify_segment_type(text)
    if segment_type != "body":
        cloned = dict(block)
        cloned["text"] = normalize_space(normalize_pdf_text(text))
        return [cloned]

    normalized_text = normalize_pdf_text(text)
    raw_lines = [" ".join(line.split()) for line in normalized_text.splitlines() if line.strip()]
    if raw_lines and is_explicit_heading(raw_lines[0]) and len(raw_lines) > 1:
        heading_block = dict(block)
        heading_block["text"] = normalize_space(raw_lines[0])
        body_text = "\n".join(raw_lines[1:])
        body_blocks = []
        for paragraph in split_body_text_into_paragraphs(body_text):
            cloned = dict(block)
            cloned["text"] = paragraph
            body_blocks.append(cloned)
        return [heading_block, *body_blocks]

    paragraphs = split_body_text_into_paragraphs(normalized_text)
    if not paragraphs:
        return []

    split_blocks = []
    for paragraph in paragraphs:
        cloned = dict(block)
        cloned["text"] = paragraph
        split_blocks.append(cloned)
    return split_blocks


def is_body_continuation(previous_text: str, current_text: str) -> bool:
    previous_text = previous_text.strip()
    current_text = current_text.strip()
    if not previous_text or not current_text:
        return False

    if TERMINAL_PUNCTUATION_RE.search(previous_text):
        return False
    if classify_segment_type(previous_text) != "body" or classify_segment_type(current_text) != "body":
        return False

    if previous_text[-1] in {",", ";", ":", "-", "–"}:
        return True

    previous_words = re.findall(r"[A-Za-z]+", previous_text.lower())
    current_words = re.findall(r"[A-Za-z]+", current_text.lower())
    previous_last_word = previous_words[-1] if previous_words else ""
    current_first_word = current_words[0] if current_words else ""

    if previous_last_word in CONTINUATION_END_WORDS:
        return True
    if current_first_word in CONTINUATION_START_WORDS:
        return True
    if re.match(r"^[a-z(\[]", current_text):
        return True

    return False


def merge_continuation_segments(segments: list[dict]) -> list[dict]:
    merged: list[dict] = []
    for segment in segments:
        if (
            merged
            and merged[-1].get("type") == "body"
            and segment.get("type") == "body"
            and is_body_continuation(merged[-1].get("source_text", ""), segment.get("source_text", ""))
        ):
            merged[-1]["source_text"] = normalize_space(
                f"{merged[-1]['source_text']} {segment['source_text']}"
            )
            page_span = list(merged[-1].get("page_span", [merged[-1].get("page_number")]))
            if segment.get("page_number") not in page_span:
                page_span.append(segment.get("page_number"))
            merged[-1]["page_span"] = page_span
            bbox_chain = list(merged[-1].get("bbox_chain", [merged[-1].get("bbox")]))
            bbox_chain.append(segment.get("bbox"))
            merged[-1]["bbox_chain"] = bbox_chain
            continue
        merged.append(segment)
    return merged


def relabel_reference_sections(segments: list[dict]) -> list[dict]:
    inside_references = False
    relabeled = []

    for segment in segments:
        cloned = dict(segment)
        text = normalize_space(cloned.get("source_text", ""))
        lowered = text.lower()
        segment_type = cloned.get("type")

        if segment_type == "heading":
            if lowered == "references":
                inside_references = True
            elif inside_references:
                inside_references = False

        if inside_references and segment_type in {"body", "metadata"}:
            cloned["type"] = "reference"

        relabeled.append(cloned)

    return relabeled


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="manifest.json generated by extract_pdf_assets.py")
    parser.add_argument("output_json", help="Output segments JSON")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    output_path = Path(args.output_json).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    segments = []
    seen_captions: set[tuple[int, str, str]] = set()

    for page in manifest.get("pages", []):
        caption_lookup = {}
        for caption in page.get("captions", []):
            caption_lookup[tuple(caption.get("caption_bbox", []))] = caption

        ordered_blocks = order_page_blocks(
            page.get("text_blocks", []),
            float(page.get("width", 0)),
            page.get("column_split"),
        )

        for block in ordered_blocks:
            for split_block in split_text_block(block):
                text = split_block.get("text", "").strip()
                caption = caption_lookup.get(tuple(split_block.get("bbox", [])))
                if caption:
                    dedupe_key = (page["page_number"], caption["kind"], caption["label"])
                    if dedupe_key in seen_captions:
                        continue
                    seen_captions.add(dedupe_key)
                    segment_type = "caption"
                    label = f"{caption['kind']}-{caption['label']}"
                else:
                    segment_type = classify_segment_type(text)
                    label = None

                segments.append(
                    {
                        "page_number": page["page_number"],
                        "type": segment_type,
                        "label": label,
                        "bbox": split_block.get("bbox"),
                        "source_text": text,
                    }
                )

    segments = merge_continuation_segments(segments)
    segments = relabel_reference_sections(segments)

    numbered_segments = []
    for counter, segment in enumerate(segments, start=1):
        numbered_segments.append(
            {
                "source_id": f"S{counter:04d}",
                **segment,
            }
        )

    payload = {
        "source_manifest": str(manifest_path),
        "segment_count": len(numbered_segments),
        "segments": numbered_segments,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
