FROM python:3.12-slim AS backend

RUN apt-get update \
    && apt-get install -y --no-install-recommends hunspell-fr-comprehensive curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY .. /app/

RUN pip install --no-cache-dir ".[api]"

# Generate wordlist from hunspell
RUN python -c "\
import pathlib, unicodedata; \
src = pathlib.Path('/usr/share/hunspell/fr.dic'); \
dst = pathlib.Path('data/fr_wordlist.txt'); \
dst.parent.mkdir(exist_ok=True); \
lines = src.read_text(encoding='latin-1').splitlines()[1:] if src.exists() else []; \
dst.write_text('\n'.join(unicodedata.normalize('NFC', w.split('/')[0]) for w in lines if w.strip()), encoding='utf-8'); \
print(f'Generated {dst} with {len(lines)} entries')"

EXPOSE 8000
CMD ["uvicorn", "ocrval.adapters.inbound.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
