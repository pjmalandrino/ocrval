import logging

from ocrval.domain.models import ChunkInput, HeuristicResult

logger = logging.getLogger(__name__)


class PerplexityScorer:
    """Pass 2 scorer — evaluates linguistic coherence via masked-LM perplexity.

    Requires the [llm] extra: ``pip install ocrval[llm]``
    """

    name: str = "perplexity"

    def __init__(
        self,
        model_name: str = "camembert-base",
        ppl_ceiling: float = 100.0,
        ppl_floor: float = 10.0,
    ) -> None:
        try:
            import lmppl
        except ImportError:
            raise ImportError(
                "Perplexity scoring requires the [llm] extra. "
                "Install with: pip install ocrval[llm]"
            )

        logger.info("Loading perplexity model '%s' ...", model_name)
        self._model = lmppl.MaskedLM(model_name)
        self._ceiling = ppl_ceiling
        self._floor = ppl_floor

    def score(self, chunk: ChunkInput) -> HeuristicResult:
        text = chunk.text.strip()

        # Too short for reliable perplexity — return neutral score
        if not text or len(text.split()) < 3:
            return HeuristicResult(value=None, score=1.0)

        ppl = self._model.get_perplexity(text)
        normalized = self._normalize(ppl)
        return HeuristicResult(value=round(ppl, 2), score=round(normalized, 4))

    def _normalize(self, ppl: float) -> float:
        """Map perplexity to 0-1 score (clamped linear interpolation).

        Low PPL (natural text)  → 1.0
        High PPL (incoherent)   → 0.0
        """
        if ppl <= self._floor:
            return 1.0
        if ppl >= self._ceiling:
            return 0.0
        return 1.0 - (ppl - self._floor) / (self._ceiling - self._floor)
