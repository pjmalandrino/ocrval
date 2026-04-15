import logging
import math

from ocrval.domain.models import ChunkInput, HeuristicResult

logger = logging.getLogger(__name__)

# Max tokens to score per chunk (truncate beyond this for speed)
_MAX_SCORE_TOKENS = 128

# How many masked variants to batch together in one forward pass
_BATCH_SIZE = 32


class PerplexityScorer:
    """Pass 2 scorer — evaluates linguistic coherence via masked-LM pseudo-perplexity.

    Computes pseudo-perplexity by masking each token one at a time and averaging
    the negative log-likelihoods. Uses CamemBERT (or any HuggingFace MLM) directly
    via ``transformers``.

    Optimized with:
    - Token truncation (first 128 tokens only — enough to assess quality)
    - Batched forward passes (32 masked variants per batch)

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
        """Compute pseudo-perplexity with batched masked forward passes.

        1. Tokenize and truncate to _MAX_SCORE_TOKENS
        2. Build all masked variants (one per non-special token)
        3. Batch them in groups of _BATCH_SIZE for efficient inference
        4. Collect log-probs → PPL = exp(-avg_log_prob)
        """
        torch = self._torch
        tokenizer = self._tokenizer
        model = self._model

        encoding = tokenizer(
            text, return_tensors="pt", truncation=True, max_length=_MAX_SCORE_TOKENS,
        )
        input_ids = encoding["input_ids"].squeeze()  # (seq_len,)
        seq_len = len(input_ids)

        # Identify maskable positions (skip special tokens like <s>, </s>)
        special_ids = set(tokenizer.all_special_ids)
        mask_positions = [i for i in range(seq_len) if input_ids[i].item() not in special_ids]

        if not mask_positions:
            return 0.0

        # Build all masked variants at once: (N, seq_len)
        original_ids = [input_ids[pos].item() for pos in mask_positions]
        all_masked = input_ids.unsqueeze(0).expand(len(mask_positions), -1).clone()
        for idx, pos in enumerate(mask_positions):
            all_masked[idx, pos] = tokenizer.mask_token_id

        # Batched forward passes
        log_probs = []
        with torch.no_grad():
            for batch_start in range(0, len(mask_positions), _BATCH_SIZE):
                batch_end = min(batch_start + _BATCH_SIZE, len(mask_positions))
                batch_ids = all_masked[batch_start:batch_end]  # (B, seq_len)

                outputs = model(batch_ids)
                logits = outputs.logits  # (B, seq_len, vocab_size)

                for i in range(batch_end - batch_start):
                    pos = mask_positions[batch_start + i]
                    orig_id = original_ids[batch_start + i]
                    token_logits = logits[i, pos]
                    log_softmax = torch.log_softmax(token_logits, dim=-1)
                    log_probs.append(log_softmax[orig_id].item())

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
