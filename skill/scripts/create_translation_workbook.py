#!/usr/bin/env python3
"""Create a translation workbook from prepared source segments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("segments_json", help="Source segments JSON")
    parser.add_argument("output_json", help="Output translation workbook JSON")
    args = parser.parse_args()

    segments_path = Path(args.segments_json).expanduser().resolve()
    output_path = Path(args.output_json).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = json.loads(segments_path.read_text(encoding="utf-8"))
    workbook = {
        "source_manifest": payload.get("source_manifest"),
        "segment_count": payload.get("segment_count"),
        "segments": [],
    }

    for segment in payload.get("segments", []):
        workbook["segments"].append(
            {
                "source_id": segment["source_id"],
                "page_number": segment.get("page_number"),
                "type": segment.get("type"),
                "label": segment.get("label"),
                "source_text": segment.get("source_text", ""),
                "translated_text": "",
                "equation_omml": "" if segment.get("type") == "equation" else None,
                "status": "pending",
                "translator_notes": "",
            }
        )

    output_path.write_text(json.dumps(workbook, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
