# ocrval

OCR output quality validation — heuristic scoring pipeline for any OCR engine.

## Install

```bash
pip install ocrval
```

## Quick start

```python
from ocrval import validate_document, validate_text

# From Docling JSON
result = validate_document(docling_json, dictionary_path="fr_wordlist.txt")

# From plain text chunks
result = validate_text(["Chunk 1 text", "Chunk 2 text"])

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
