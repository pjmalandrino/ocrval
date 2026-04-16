from ocrval.domain.models import ChunkInput
from ocrval.scorers.repetition import RepetitionScorer


def test_unique_chunks():
    chunks = [ChunkInput(ref=f"#/{i}", label="p", text=f"Unique text number {i}") for i in range(5)]
    scorer = RepetitionScorer(min_occurrences=3)
    scorer.prepare(chunks)

    for chunk in chunks:
        result = scorer.score(chunk)
        assert result.score == 1.0


def test_repeated_chunks():
    repeated = ChunkInput(ref="#/0", label="p", text="Page 1 of 10")
    chunks = [ChunkInput(ref=f"#/{i}", label="p", text="Page 1 of 10") for i in range(5)]
    scorer = RepetitionScorer(min_occurrences=3)
    scorer.prepare(chunks)

    result = scorer.score(repeated)
    assert result.score == 0.0
    assert result.value == 5


def test_empty_chunk(empty_chunk):
    scorer = RepetitionScorer(min_occurrences=3)
    scorer.prepare([empty_chunk])
    result = scorer.score(empty_chunk)
    assert result.score == 1.0
