# ocrval

OCR output quality validation — heuristic scoring pipeline for any OCR engine.

## Install

```bash
pip install ocrval
```

## Quick start

```python
from ocrval import validate_document, validate_text

# From Docling JSON — dictionary auto-downloaded and cached
result = validate_document(docling_json, lang="fr")

# With domain-specific words
result = validate_document(
    docling_json,
    lang="fr",
    custom_words=["bornier", "domotique"],
)

# From plain text chunks
result = validate_text(["Chunk 1 text", "Chunk 2 text"], lang="fr")

print(result.overall_score)  # 0.82
print(result.bucket)         # "good"
```

## API demo server

```bash
pip install ocrval[api]
uvicorn ocrval.adapters.inbound.api.app:app --port 8000
```

## License

MIT
