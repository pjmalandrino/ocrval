import logging
import math

from ocrval.domain.models import ChunkInput, HeuristicResult

logger = logging.getLogger(__name__)


class PerplexityScorer:
    """Pass 2 scorer — evaluates linguistic coherence via masked-LM pseudo-perplexity.

    Computes pseudo-perplexity by masking each token one at a time and averaging
    the negative log-likelihoods. Uses CamemBERT (or any HuggingFace MLM) directly
    via ``transformers``.

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
            import torch
            from transformers import AutoModelForMaskedLM, AutoTokenizer
        except ImportError:
            raise ImportError(
                "Perplexity scoring requires the [llm] extra. "
                "Install with: pip install ocrval[llm]"
            )

        logger.info("Loading perplexity model '%s' ...", model_name)
        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._model = AutoModelForMaskedLM.from_pretrained(model_name)
        self._model.eval()
        self._torch = torch
        self._ceiling = ppl_ceiling
        self._floor = ppl_floor

    def score(self, chunk: ChunkInput) -> HeuristicResult:
        text = chunk.text.strip()

        # Too short for reliable perplexity — return neutral score
        if not text or len(text.split()) < 3:
            return HeuristicResult(value=None, score=1.0)

        ppl = self._compute_pseudo_ppl(text)
        normalized = self._normalize(ppl)
        return HeuristicResult(value=round(ppl, 2), score=round(normalized, 4))

    def _compute_pseudo_ppl(self, text: str) -> float:
        """Compute pseudo-perplexity by masking each token one at a time.

        For each non-special token, mask it, run the model, and record
        the log-probability of the original token. PPL = exp(-avg_log_prob).
        """
        torch = self._torch
        tokenizer = self._tokenizer
        model = self._model

        encoding = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        input_ids = encoding["input_ids"].squeeze()  # shape: (seq_len,)

        # Identify maskable positions (skip special tokens like <s>, </s>)
        special_ids = set(tokenizer.all_special_ids)
        mask_positions = [i for i in range(len(input_ids)) if input_ids[i].item() not in special_ids]

        if not mask_positions:
            return 0.0

        log_probs = []

        with torch.no_grad():
            for pos in mask_positions:
                # Clone and mask one token
                masked_ids = input_ids.clone().unsqueeze(0)  # (1, seq_len)
                original_id = masked_ids[0, pos].item()
                masked_ids[0, pos] = tokenizer.mask_token_id

                outputs = model(masked_ids)
                logits = outputs.logits[0, pos]  # (vocab_size,)

                # Log-softmax to get log-probabilities
                log_softmax = torch.log_softmax(logits, dim=-1)
                log_prob = log_softmax[original_id].item()
                log_probs.append(log_prob)

        avg_neg_log_prob = -sum(log_probs) / len(log_probs)
        return math.exp(avg_neg_log_prob)

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
