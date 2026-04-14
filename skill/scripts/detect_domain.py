#!/usr/bin/env python3
"""Infer a paper domain from title/abstract/body text and suggest termbases."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter


DOMAIN_RULES = {
    "medicine": {
        "keywords": [
            "clinical",
            "patient",
            "disease",
            "diagnosis",
            "therapy",
            "radiology",
            "tumor",
            "hospital",
            "medical",
            "biomarker",
        ],
        "termbases": ["MeSH", "UMLS", "WHO terminology", "ICD/SNOMED CT"],
    },
    "biology": {
        "keywords": [
            "protein",
            "genome",
            "cell",
            "gene",
            "pathway",
            "microscopy",
            "metabolism",
            "biological",
            "enzyme",
            "rna",
        ],
        "termbases": ["MeSH", "Gene Ontology", "UniProt", "NCBI terminology"],
    },
    "chemistry-materials": {
        "keywords": [
            "catalyst",
            "polymer",
            "molecule",
            "compound",
            "nanoparticle",
            "crystal",
            "alloy",
            "material",
            "electrolyte",
            "synthesis",
        ],
        "termbases": ["IUPAC Gold Book", "NIST chemistry", "materials glossaries"],
    },
    "physics": {
        "keywords": [
            "quantum",
            "photon",
            "lattice",
            "thermodynamic",
            "spin",
            "spectroscopy",
            "hamiltonian",
            "optical",
            "wavefunction",
            "field theory",
        ],
        "termbases": ["NIST term references", "APS/AIP glossaries"],
    },
    "electrical-engineering": {
        "keywords": [
            "signal",
            "modulation",
            "channel",
            "antenna",
            "wireless",
            "communication",
            "beamforming",
            "circuit",
            "radar",
            "ofdm",
        ],
        "termbases": ["IEEE Taxonomy", "ITU terminology", "standards glossaries"],
    },
    "computer-science-ai": {
        "keywords": [
            "neural network",
            "transformer",
            "benchmark",
            "dataset",
            "reinforcement learning",
            "segmentation",
            "classification",
            "optimization",
            "algorithm",
            "inference",
        ],
        "termbases": ["IEEE Taxonomy", "ACM CCS", "official model/dataset docs"],
    },
    "economics-social-science": {
        "keywords": [
            "policy",
            "survey",
            "household",
            "firm",
            "market",
            "education",
            "behavior",
            "regression",
            "employment",
            "governance",
        ],
        "termbases": ["OECD glossary", "World Bank glossaries", "APA/ERIC terminology"],
    },
}

ARXIV_HINTS = {
    "cs.": "computer-science-ai",
    "stat.ml": "computer-science-ai",
    "eess.": "electrical-engineering",
    "physics.": "physics",
    "cond-mat.": "physics",
    "q-bio.": "biology",
    "q-fin.": "economics-social-science",
}


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9.+/-]*", text.lower())


def score_domains(text: str) -> Counter:
    words = tokenize(text)
    normalized = " ".join(words)
    scores: Counter = Counter()
    for domain, config in DOMAIN_RULES.items():
        for keyword in config["keywords"]:
            occurrences = normalized.count(keyword.lower())
            if occurrences:
                scores[domain] += occurrences
    return scores


def apply_arxiv_hint(scores: Counter, arxiv_category: str | None) -> None:
    if not arxiv_category:
        return
    category = arxiv_category.strip().lower()
    for prefix, domain in ARXIV_HINTS.items():
        if category.startswith(prefix):
            scores[domain] += 3
            return


def choose_domain(scores: Counter) -> str:
    if not scores:
        return "general-scientific"
    return scores.most_common(1)[0][0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", default="", help="Paper title")
    parser.add_argument("--abstract", default="", help="Paper abstract")
    parser.add_argument("--text-file", help="Path to a text file with paper content")
    parser.add_argument("--arxiv-category", help="Optional arXiv category hint")
    args = parser.parse_args()

    body = ""
    if args.text_file:
        with open(args.text_file, "r", encoding="utf-8") as f:
            body = f.read()

    text = "\n".join(part for part in [args.title, args.abstract, body] if part.strip())
    scores = score_domains(text)
    apply_arxiv_hint(scores, args.arxiv_category)
    domain = choose_domain(scores)

    payload = {
        "selected_domain": domain,
        "scores": dict(scores.most_common()),
        "suggested_termbases": DOMAIN_RULES.get(domain, {}).get(
            "termbases", ["IATE", "field-specific society terminology"]
        ),
        "note": "Use user-provided glossary first. Mixed-domain papers may need two active termbases.",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
