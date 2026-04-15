from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class ScorerWeights(BaseModel):
    special_char_ratio: float = 0.25
    dictionary_ratio: float = 0.35
    short_chunk: float = 0.20
    line_repetition: float = 0.20
    perplexity: float = 0.30


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OCV_",
        env_nested_delimiter="__",
    )

    # Thresholds
    special_char_threshold: float = 0.15
    dictionary_oov_threshold: float = 0.30
    short_chunk_min_words: int = 3
    repetition_min_occurrences: int = 3

    # Bucketing
    bucket_good_threshold: float = 0.75
    bucket_bad_threshold: float = 0.40

    # Weights
    weights: ScorerWeights = ScorerWeights()

    # Dictionary
    lang: str | None = "fr"
    custom_words: list[str] | None = None

    # Pass 2 — perplexity (requires [llm] extra)
    pass2_enabled: bool = False
    perplexity_model: str = "camembert-base"
    perplexity_ceiling: float = 100.0
    perplexity_floor: float = 10.0


settings = Settings()
