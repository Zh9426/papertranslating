#!/usr/bin/env python3
"""Validate a translation workbook for completeness and ordering."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook_json", help="Translation workbook JSON")
    parser.add_argument("--segments", help="Optional source segments JSON")
    args = parser.parse_args()

    workbook_path = Path(args.workbook_json).expanduser().resolve()
    workbook = json.loads(workbook_path.read_text(encoding="utf-8"))

    report = {
        "workbook": str(workbook_path),
        "segment_count": len(workbook.get("segments", [])),
        "missing_translation_ids": [],
        "empty_translation_ids": [],
        "omitted_segment_ids": [],
        "equation_segments_missing_omml": [],
        "duplicate_source_ids": [],
        "out_of_order": False,
    }

    seen = set()
    previous = ""
    for segment in workbook.get("segments", []):
        source_id = segment.get("source_id", "")
        translated = (segment.get("translated_text") or "").strip()
        status = segment.get("status", "")

        if source_id in seen:
            report["duplicate_source_ids"].append(source_id)
        seen.add(source_id)

        if previous and source_id < previous:
            report["out_of_order"] = True
        previous = source_id

        if not source_id:
            report["missing_translation_ids"].append(source_id)
        if status == "omitted":
            report["omitted_segment_ids"].append(source_id)
        if status != "omitted" and not translated:
            report["empty_translation_ids"].append(source_id)
        if segment.get("type") == "equation" and status != "omitted":
            omml = (segment.get("equation_omml") or "").strip()
            if not omml:
                report["equation_segments_missing_omml"].append(source_id)

    if args.segments:
        segments_path = Path(args.segments).expanduser().resolve()
        source = json.loads(segments_path.read_text(encoding="utf-8"))
        source_ids = [seg["source_id"] for seg in source.get("segments", [])]
        workbook_ids = [seg.get("source_id") for seg in workbook.get("segments", [])]
        report["source_ids_missing_from_workbook"] = [sid for sid in source_ids if sid not in workbook_ids]
        report["extra_workbook_ids"] = [sid for sid in workbook_ids if sid not in source_ids]

    print(json.dumps(report, ensure_ascii=False, indent=2))
    blocking_issues = [
        report["missing_translation_ids"],
        report["empty_translation_ids"],
        report["omitted_segment_ids"],
        report["equation_segments_missing_omml"],
        report["duplicate_source_ids"],
        report.get("source_ids_missing_from_workbook", []),
        report.get("extra_workbook_ids", []),
    ]
    if report["out_of_order"] or any(blocking_issues):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
