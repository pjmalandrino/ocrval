from ocrval.domain.models import ChunkInput, ChunkResult
from ocrval.domain.ports import Scorer


class ScoringPipeline:
    def __init__(self) -> None:
        self._scorers: list[Scorer] = []

    def register(self, scorer: Scorer) -> None:
        self._scorers.append(scorer)

    @property
    def scorer_names(self) -> list[str]:
        return [s.name for s in self._scorers]

    def run(self, chunks: list[ChunkInput]) -> list[ChunkResult]:
        results: list[ChunkResult] = []
        for chunk in chunks:
            heuristics = {}
            for scorer in self._scorers:
                heuristics[scorer.name] = scorer.score(chunk)
            results.append(ChunkResult(chunk=chunk, heuristics=heuristics))
        return results
