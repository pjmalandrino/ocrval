from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class ScorerWeights(BaseModel):
    special_char_ratio: float = 0.20
    dictionary_ratio: float = 0.30
    regex_artifacts: float = 0.15
    short_chunk: float = 0.15
    line_repetition: float = 0.20


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

    # Regex artifact detection
    regex_artifact_threshold: float = 0.10
    custom_regex_patterns: list[list[str]] | None = None  # [["name", "regex"], ...]


settings = Settings()
