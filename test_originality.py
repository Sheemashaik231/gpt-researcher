# test_originality.py
from originality_guard import check_originality, build_rewrite_instructions

sources = {
    "https://example.org/rag": (
        "Retrieval augmented generation combines a language model with an external "
        "knowledge base so that answers are grounded in retrieved documents rather "
        "than only in the model parameters."
    )
}

draft = """# Report

Retrieval augmented generation combines a language model with an external knowledge base so that answers are grounded in retrieved documents rather than only in the model parameters.

In practice the approach trades extra latency for fresher answers, and its quality depends heavily on how well the retriever ranks relevant passages for each query."""

report = check_originality(draft, sources)
print("Originality score:", report["originality_score"])
print("Flagged paragraphs:", report["flagged_count"])
print()
print(build_rewrite_instructions(report))