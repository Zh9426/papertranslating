# Termbase Selection

Use the user's stated field first. If absent, infer from title, abstract, keywords, arXiv category, venue, and introduction.

## Selection policy

1. Prefer the user's own glossary if provided.
2. Prefer the contribution domain over the surface application domain.
3. When the paper crosses domains, keep two termbases active at once.
4. Record every non-obvious term choice in a glossary table before bulk translation.

## Recommended termbase families

### General multilingual scientific terms

- IATE: broad multilingual terminology, useful for cross-domain baseline checks
- Wikidata / Wikipedia category pages: useful only as a weak disambiguation aid, never as the sole authority

### Medicine and clinical research

- MeSH
- UMLS
- WHO terminology resources
- ICD / SNOMED CT when disease or clinical coding language matters

### Biology and life sciences

- MeSH
- Gene Ontology
- UniProt glossary pages
- NCBI Bookshelf terminology pages

### Chemistry and materials

- IUPAC Gold Book
- NIST chemistry references
- publisher glossaries for materials subfields when available

### Physics and applied physics

- NIST term references
- APS / AIP glossaries when available
- domain textbooks or society references for stable translations

### Electrical engineering, signal processing, communications

- IEEE Taxonomy
- ITU terminology
- signal-processing textbooks and standards terminology when the paper is standards-adjacent

### Computer science and AI

- IEEE Taxonomy
- ACM CCS
- model or benchmark official docs for canonical names
- keep benchmark names, model names, repo names, and dataset names untranslated unless a standard Chinese form is dominant

### Economics, management, and social science

- OECD glossary
- World Bank glossaries
- APA / ERIC terminology where relevant

## arXiv and venue hints

- `cs.CV`, `cs.LG`, `cs.AI`: computer vision / machine learning / AI
- `eess.SP`, `cs.IT`: signal processing / information theory / communications
- `physics.app-ph`, `cond-mat.*`: applied physics / materials / condensed matter
- `q-bio.*`, `stat.ML` with biomedical context: biology or biostatistics

## Glossary minimum schema

Use a table or JSON with these fields:

- `source_term`
- `target_term`
- `domain`
- `status`: approved / uncertain / keep-original
- `note`

## Conflict handling

- If two termbases disagree, prefer the one aligned with the paper's contribution domain.
- If there is no stable Chinese rendering, keep the English term and explain it on first use.
- If the term is a named method, dataset, theorem, or protocol, default to keeping the canonical name.
