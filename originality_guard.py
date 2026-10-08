# originality_guard.py
"""Checks a draft against fetched source texts using n-gram overlap.

Flags paragraphs that copy too much source wording, so the writer can be
asked to rewrite them as original synthesis with a citation or a short quote.
"""
import re

NGRAM_SIZE = 5          # words per sequence compared
FLAG_THRESHOLD = 0.25   # paragraph is flagged if >25% of its sequences match a source
MIN_WORDS = 12          # skip very short paragraphs, headings and reference lines


def _words(text):
    return re.findall(r"[a-z0-9']+", text.lower())


def _ngrams(words, n=NGRAM_SIZE):
    if len(words) < n:
        return set()
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def _strip_quotes(text):
    """Remove quoted passages: short quoted excerpts are allowed."""
    return re.sub(r'["\u201c][^"\u201d]{1,400}["\u201d]', " ", text)


def split_paragraphs(text):
    parts = [p.strip() for p in re.split(r"\n\s*\n", text)]
    return [p for p in parts if p]


def check_originality(draft, sources, threshold=FLAG_THRESHOLD):
    """
    draft:   the full draft text (string)
    sources: dict mapping a source id or URL -> the scraped text of that source
    Returns a dict with overall score (0-100), per-paragraph details and flagged ones.
    """
    source_grams = {sid: _ngrams(_words(txt)) for sid, txt in sources.items()}
    results = []

    for idx, para in enumerate(split_paragraphs(draft)):
        if para.startswith("#") or para.startswith("- ") or para.startswith("["):
            continue
        words = _words(_strip_quotes(para))
        if len(words) < MIN_WORDS:
            continue
        grams = _ngrams(words)
        if not grams:
            continue

        best_source, best_shared = None, 0
        matched = set()
        for sid, sgrams in source_grams.items():
            shared = grams & sgrams
            matched |= shared
            if len(shared) > best_shared:
                best_source, best_shared = sid, len(shared)

        overlap = len(matched) / len(grams)
        results.append({
            "paragraph_index": idx,
            "text": para,
            "overlap": round(overlap, 3),
            "best_source": best_source,
            "flagged": overlap > threshold,
            "words": len(words),
        })

    total_words = sum(r["words"] for r in results) or 1
    weighted_overlap = sum(r["overlap"] * r["words"] for r in results) / total_words
    flagged = [r for r in results if r["flagged"]]

    return {
        "originality_score": round((1 - weighted_overlap) * 100, 1),
        "paragraphs_checked": len(results),
        "flagged_count": len(flagged),
        "flagged": flagged,
        "all_paragraphs": results,
    }


def build_rewrite_instructions(report):
    """Turns the flagged paragraphs into instructions for the writer agent."""
    if not report["flagged"]:
        return ""
    lines = [
        "Rewrite ONLY the paragraphs below as original synthesis in your own words.",
        "Compare, analyse limitations and draw conclusions instead of restating the source.",
        "Where wording matters, use a short quoted excerpt in quotation marks with a citation.",
        "",
    ]
    for r in report["flagged"]:
        lines.append(
            f"- Paragraph {r['paragraph_index']} overlaps {int(r['overlap'] * 100)}% "
            f"with source: {r['best_source']}"
        )
        lines.append(f"  Text: {r['text'][:300]}")
    return "\n".join(lines)