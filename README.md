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

## Docker

A prebuilt image is published to GitHub Container Registry on every push to `main`.
It bundles the REST API **and** the Vue demo frontend served on the same port.

```bash
# Pull the latest image
docker pull ghcr.io/pjmalandrino/ocrval:latest

# Run it — API on http://localhost:8000, frontend on http://localhost:8000/
docker run --rm -p 8000:8000 ghcr.io/pjmalandrino/ocrval:latest
```

Endpoints:

- `GET  /health` — health check
- `POST /v1/validate` — validation endpoint (accepts Docling JSON **or** `DoclingDocument`)
- `GET  /` — Vue demo UI (open in a browser)

### Consume the API with `curl`

The endpoint accepts two JSON shapes auto-detected by a top-level key.

**1. Docling chunking response** (key: `chunks`)

```bash
curl -X POST http://localhost:8000/v1/validate \
  -H "Content-Type: application/json" \
  -d '{
    "name": "invoice-42.pdf",
    "chunks": [
      {
        "text": "Facture n° 2024-0042 émise le 12 mars 2024.",
        "block_type": "paragraph",
        "page_numbers": [1],
        "doc_items": ["#/texts/0"]
      },
      {
        "text": "Mnt t0tal : |23,45 EUR  ||| garbageee",
        "block_type": "paragraph",
        "page_numbers": [1]
      }
    ]
  }'
```

**2. DoclingDocument** (key: `texts`)

```bash
curl -X POST http://localhost:8000/v1/validate \
  -H "Content-Type: application/json" \
  -d '{
    "name": "report.pdf",
    "texts": [
      {
        "text": "Rapport annuel 2024 — synthèse exécutive.",
        "self_ref": "#/texts/0",
        "label": "title",
        "prov": [{"page_no": 1}]
      },
      {
        "text": "Le chiffre d affaires progresse de 12%.",
        "self_ref": "#/texts/1",
        "label": "paragraph",
        "prov": [{"page_no": 1}]
      }
    ]
  }'
```

**Optional query parameter** — override the `short_chunk` scorer threshold:

```bash
curl -X POST "http://localhost:8000/v1/validate?short_chunk_min_words=5" \
  -H "Content-Type: application/json" \
  -d @mydoc.json
```

**Response shape** (abridged):

```json
{
  "document_id": "invoice-42.pdf",
  "overall_score": 0.72,
  "bucket": "uncertain",
  "chunk_scores": [
    {
      "chunk_ref": "#/texts/0",
      "label": "paragraph",
      "page_no": 1,
      "text_preview": "Facture n° 2024-0042 …",
      "quality_score": 0.91,
      "usability_score": 0.80,
      "chunk_score": 0.86,
      "bucket": "good",
      "scores": {
        "special_char_ratio": 0.98,
        "dictionary_ratio": 0.88,
        "regex_artifacts": 1.00,
        "short_chunk": 1.00,
        "line_repetition": 1.00
      }
    }
  ],
  "flags": ["low_dictionary_ratio"],
  "scorer_versions": {"special_char_ratio": "1.0", "...": "..."}
}
```

`bucket` is one of `good`, `uncertain`, `bad`.

### Build locally

```bash
docker build -t ocrval:local .
docker run --rm -p 8000:8000 ocrval:local
```

## License

MIT
