# Translation Discipline

This skill is for translation, not explanation, retelling, or literature review writing.

## Core rule

Translate from the source paragraph's point of view. Do not replace the source voice with your own narration.

## Required scientific register

- The default Chinese output must read like a formal research paper, not a lecture note, blog post, or oral explanation.
- Keep the tone restrained, precise, and evidence-oriented.
- Preserve hedging such as `may`, `might`, `can`, `could`, `suggest`, `indicate`, and `is likely to` instead of overstating certainty.
- Prefer formal academic wording over conversational paraphrase.
- Keep evaluative language aligned with the source. Do not inject praise, emphasis, or dramatic framing that the source does not contain.

## Mandatory paragraph fidelity

- Preserve section order exactly.
- Preserve paragraph order exactly.
- Default rule: one source paragraph or source block becomes one target paragraph.
- Stop and fix segmentation before translating if one `source_id` clearly contains multiple source paragraphs.
- Do not merge adjacent source paragraphs unless the source itself was split only by PDF layout artifacts and the combined text is clearly one paragraph.
- Do not split one source paragraph into multiple target paragraphs unless the user explicitly asks for readability-oriented reflow.
- Keep captions as captions, not body paragraphs.
- Keep headings as headings, not body paragraphs.
- Do not let a whole column-sized PDF block pass through as one translation unit without checking its paragraph granularity.

## Forbidden drift patterns

Avoid these unless the source explicitly says the same thing:

- `作者指出`
- `作者认为`
- `作者团队`
- `作者进一步`
- `本文提出`
- `本文还`
- `文中指出`
- `该研究表明`
- `研究者发现`

These are common signs that the output has shifted from translation into summary or explanatory prose.

## Forbidden register drift

Avoid colloquial or teacher-like phrasing such as:

- `说白了`
- `简单来说`
- `通俗地说`
- `打个比方`
- `大家知道`
- `总的来说`
- `总之`
- `其实`
- `相当于`
- `就像`

Avoid rhetorical or performative framing such as:

- asking rhetorical questions
- using exclamation marks unless the source does so
- turning cautious source claims into assertive conclusions
- replacing technical precision with vague summary words such as `很多`, `非常厉害`, or `很有意思`

## What to do instead

- If the source says `we propose`, translate that directly as the paper's own claim.
- If the source says `this work demonstrates`, translate that directly.
- If the source is impersonal, keep it impersonal.
- If the source uses first person plural, preserve the paper's authorial voice rather than replacing it with third-person commentary.
- If the source is cautious, preserve that caution in Chinese.

## Omission policy

- Do not omit qualifiers, caveats, contrast clauses, or parenthetical constraints.
- Do not compress multiple examples into one generalized sentence.
- Do not drop references to figures, equations, datasets, parameter ranges, or experimental settings.
- If a sentence is hard to translate, keep it faithful first and polish second.

## Compression is not allowed by default

Never shorten because the translated Chinese "looks repetitive" or because you think the idea can be said more compactly.

Translation quality is measured by fidelity first, elegance second.

## Practical workflow

1. Build a source segment list from the extracted manifest.
2. Validate that no prepared body segment is obviously oversized before translating.
3. Translate segment by segment in a formal scientific register.
4. Keep a stable `source_id` for every translated segment.
5. Reassemble only after the segment translation is complete.
6. Run fidelity validation before DOCX handoff.

## Acceptable adaptation

These are allowed:

- reorder within a sentence when Chinese grammar requires it
- expand an abbreviation on first use
- normalize punctuation
- smooth obvious PDF hyphenation artifacts

These are not allowed:

- converting technical prose into commentary
- replacing the source voice with "the authors say..." narration
- deleting repetitive-looking detail
- rewriting the logic flow into your own structure
- shifting from paper style to conversational Chinese
