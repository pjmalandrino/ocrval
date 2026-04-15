from ocrval.domain.models import Bucket, ChunkResult, HeuristicResult


def aggregate_chunk(
    heuristics: dict[str, HeuristicResult],
    weights: dict[str, float],
) -> float:
    """Weighted average of individual heuristic scores -> 0-1."""
    total_weight = 0.0
    weighted_sum = 0.0
    for name, result in heuristics.items():
        w = weights.get(name, 0.0)
        weighted_sum += result.score * w
        total_weight += w
    if total_weight == 0:
        return 0.0
    return weighted_sum / total_weight


def classify(score: float, good_threshold: float, bad_threshold: float) -> Bucket:
    """Map a 0-1 score to a bucket."""
    if score >= good_threshold:
        return Bucket.GOOD
    if score < bad_threshold:
        return Bucket.BAD
    return Bucket.UNCERTAIN


def aggregate_document(chunk_results: list[ChunkResult], weights: dict[str, float]) -> float:
    """Weighted average of chunk scores, weighted by text length."""
    total_len = 0
    weighted_sum = 0.0
    for cr in chunk_results:
        text_len = max(len(cr.chunk.text), 1)
        chunk_score = aggregate_chunk(cr.heuristics, weights)
        weighted_sum += chunk_score * text_len
        total_len += text_len
    if total_len == 0:
        return 0.0
    return weighted_sum / total_len


def generate_flags(chunk_results: list[ChunkResult], weights: dict[str, float]) -> list[str]:
    """Generate human-readable flags for notable issues."""
    flags: list[str] = []

    short_count = sum(
        1
        for cr in chunk_results
        if "short_chunk" in cr.heuristics and cr.heuristics["short_chunk"].value is True
    )
    if short_count > 0:
        flags.append(f"{short_count} chunk(s) flagged as short/empty")

    repeated_count = sum(
        1
        for cr in chunk_results
        if "line_repetition" in cr.heuristics and cr.heuristics["line_repetition"].score < 0.5
    )
    if repeated_count > 0:
        flags.append(f"{repeated_count} chunk(s) detected as repeated lines")

    bad_pages: set[int] = set()
    for cr in chunk_results:
        if (
            "special_char_ratio" in cr.heuristics
            and cr.heuristics["special_char_ratio"].score < 0.3
            and cr.chunk.page_no is not None
        ):
            bad_pages.add(cr.chunk.page_no)
    for page in sorted(bad_pages):
        flags.append(f"High special char ratio on page {page}")

    return flags
