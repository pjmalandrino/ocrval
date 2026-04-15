from ocrval.domain.models import Bucket, HeuristicResult
from ocrval.pipeline.aggregator import aggregate_chunk, classify
from ocrval.pipeline.registry import ScoringPipeline
from ocrval.scorers.short_chunk import ShortChunkScorer
from ocrval.scorers.special_char import SpecialCharScorer


def test_pipeline_runs_all_scorers(good_chunk):
    pipeline = ScoringPipeline()
    pipeline.register(SpecialCharScorer())
    pipeline.register(ShortChunkScorer())

    results = pipeline.run([good_chunk])
    assert len(results) == 1
    assert "special_char_ratio" in results[0].heuristics
    assert "short_chunk" in results[0].heuristics


def test_aggregate_chunk():
    heuristics = {
        "a": HeuristicResult(value=0.1, score=0.9),
        "b": HeuristicResult(value=0.2, score=0.5),
    }
    weights = {"a": 0.6, "b": 0.4}
    score = aggregate_chunk(heuristics, weights)
    expected = (0.9 * 0.6 + 0.5 * 0.4) / (0.6 + 0.4)
    assert abs(score - expected) < 0.001


def test_classify():
    assert classify(0.8, 0.75, 0.40) == Bucket.GOOD
    assert classify(0.5, 0.75, 0.40) == Bucket.UNCERTAIN
    assert classify(0.3, 0.75, 0.40) == Bucket.BAD
