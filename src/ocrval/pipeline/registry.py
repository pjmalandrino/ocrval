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

    def prepare(self, chunks: list[ChunkInput]) -> None:
        """Call prepare() on scorers that need document-level context (e.g. RepetitionScorer)."""
        for scorer in self._scorers:
            if hasattr(scorer, "prepare") and callable(scorer.prepare):
                scorer.prepare(chunks)

    def run(
        self,
        chunks: list[ChunkInput],
        exclude: set[str] | None = None,
    ) -> list[ChunkResult]:
        self.prepare(chunks)
        results: list[ChunkResult] = []
        active_scorers = [s for s in self._scorers if not exclude or s.name not in exclude]
        for chunk in chunks:
            heuristics = {}
            for scorer in active_scorers:
                heuristics[scorer.name] = scorer.score(chunk)
            results.append(ChunkResult(chunk=chunk, heuristics=heuristics))
        return results

    def score_single(self, chunk: ChunkInput, scorer_name: str) -> dict[str, any]:
        """Run a single scorer on a single chunk. Used for selective pass 2."""
        for scorer in self._scorers:
            if scorer.name == scorer_name:
                return {scorer_name: scorer.score(chunk)}
        return {}
