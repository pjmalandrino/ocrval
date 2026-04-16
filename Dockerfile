# ── Stage 1: Build frontend ──────────────────────────────────────────────
FROM node:20-slim AS frontend-build

WORKDIR /app/frontend
COPY demo/frontend/package.json demo/frontend/package-lock.json* ./
RUN npm ci --ignore-scripts 2>/dev/null || npm install
COPY demo/frontend/ ./
RUN npm run build

# ── Stage 2: Python API ─────────────────────────────────────────────────
FROM python:3.12-slim

LABEL maintainer="PJ Malandrino"
LABEL description="ocrval — OCR output quality validation API"

WORKDIR /app

# Install the package with API extra
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir ".[api]"

# Copy built frontend static files
COPY --from=frontend-build /app/frontend/dist /app/static

# Expose port
ENV PORT=8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run with uvicorn, serving static files from /app/static
CMD ["uvicorn", "ocrval.adapters.inbound.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
