<script setup>
import { ref } from 'vue'

const input = ref('')
const inputMode = ref('json')
const result = ref(null)
const loading = ref(false)
const error = ref(null)
const shortChunkMinWords = ref(3)

const sampleJson = JSON.stringify({
  name: "exemple_facture.pdf",
  texts: [
    {
      self_ref: "#/texts/0",
      label: "title",
      text: "FACTURE N° 2024-0042",
      prov: [{ page_no: 1 }]
    },
    {
      self_ref: "#/texts/1",
      label: "paragraph",
      text: "Le montant total de la facture est de mille deux cents euros toutes taxes comprises.",
      prov: [{ page_no: 1 }]
    },
    {
      self_ref: "#/texts/2",
      label: "paragraph",
      text: "L€$ c0nd!t!0n$ g€n€r@l€$ d€ v€nt€ $0nt @pp|!c@bl€$ @ t0ut€$ |€$ c0mm@nd€$.",
      prov: [{ page_no: 2 }]
    },
    {
      self_ref: "#/texts/3",
      label: "paragraph",
      text: "",
      prov: [{ page_no: 2 }]
    },
    {
      self_ref: "#/texts/4",
      label: "section_header",
      text: "Page 1 sur 3",
      prov: [{ page_no: 1 }]
    },
    {
      self_ref: "#/texts/5",
      label: "section_header",
      text: "Page 1 sur 3",
      prov: [{ page_no: 2 }]
    },
    {
      self_ref: "#/texts/6",
      label: "section_header",
      text: "Page 1 sur 3",
      prov: [{ page_no: 3 }]
    }
  ],
  tables: []
}, null, 2)

function loadSample() {
  input.value = sampleJson
  inputMode.value = 'json'
}

function buildPayload() {
  if (inputMode.value === 'json') {
    return JSON.parse(input.value)
  }
  // MD mode: wrap markdown lines as Docling-like JSON
  const lines = input.value.split('\n').filter(l => l.trim())
  return {
    name: 'pasted_document.md',
    texts: lines.map((line, i) => ({
      self_ref: `#/texts/${i}`,
      label: line.startsWith('#') ? 'section_header' : 'paragraph',
      text: line.replace(/^#+\s*/, ''),
      prov: [{ page_no: 1 }],
    })),
    tables: [],
  }
}

async function validate() {
  error.value = null
  result.value = null
  loading.value = true

  try {
    const payload = buildPayload()
    const params = new URLSearchParams()
    if (shortChunkMinWords.value !== 3) {
      params.set('short_chunk_min_words', shortChunkMinWords.value)
    }
    const qs = params.toString() ? `?${params.toString()}` : ''
    const resp = await fetch(`/v1/validate${qs}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!resp.ok) {
      const detail = await resp.json().catch(() => ({}))
      throw new Error(detail.detail || `HTTP ${resp.status}`)
    }
    result.value = await resp.json()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function bucketColor(bucket) {
  return bucket === 'good' ? 'var(--good)' : bucket === 'bad' ? 'var(--bad)' : 'var(--uncertain)'
}
function bucketBg(bucket) {
  return bucket === 'good' ? 'var(--good-bg)' : bucket === 'bad' ? 'var(--bad-bg)' : 'var(--uncertain-bg)'
}
function scoreBarWidth(score) {
  return `${Math.round(score * 100)}%`
}
</script>

<template>
  <header class="header">
    <h1>OCR Validator</h1>
    <p class="subtitle">Colle un output Docling (JSON ou Markdown) pour analyser la qualite</p>
  </header>

  <div class="input-section">
    <div class="toolbar">
      <div class="mode-switch">
        <button
          :class="['mode-btn', { active: inputMode === 'json' }]"
          @click="inputMode = 'json'"
        >JSON</button>
        <button
          :class="['mode-btn', { active: inputMode === 'md' }]"
          @click="inputMode = 'md'"
        >Markdown</button>
      </div>
      <button class="sample-btn" @click="loadSample">Charger un exemple</button>
    </div>

    <textarea
      v-model="input"
      class="editor"
      :placeholder="inputMode === 'json'
        ? 'Colle ici le JSON Docling (DoclingDocument)...'
        : 'Colle ici le Markdown extrait par Docling...'"
      spellcheck="false"
    ></textarea>

    <div class="settings-panel">
      <label class="setting">
        <span class="setting-label">Short chunk min words</span>
        <div class="setting-control">
          <input
            type="range"
            v-model.number="shortChunkMinWords"
            min="1"
            max="20"
            step="1"
          />
          <span class="setting-value">{{ shortChunkMinWords }}</span>
        </div>
      </label>
    </div>

    <button
      class="validate-btn"
      :disabled="!input.trim() || loading"
      @click="validate"
    >
      <span v-if="loading" class="spinner"></span>
      <span v-else>Valider</span>
    </button>

    <p v-if="error" class="error-msg">{{ error }}</p>
  </div>

  <div v-if="result" class="results">
    <div class="overall-card" :style="{ borderColor: bucketColor(result.bucket) }">
      <div class="overall-header">
        <div>
          <span class="doc-name">{{ result.document_id }}</span>
          <span class="badge" :style="{ background: bucketBg(result.bucket), color: bucketColor(result.bucket) }">
            {{ result.bucket.toUpperCase() }}
          </span>
        </div>
        <span class="overall-score" :style="{ color: bucketColor(result.bucket) }">
          {{ (result.overall_score * 100).toFixed(1) }}%
        </span>
      </div>
      <div class="score-bar-track">
        <div
          class="score-bar-fill"
          :style="{ width: scoreBarWidth(result.overall_score), background: bucketColor(result.bucket) }"
        ></div>
      </div>
      <div v-if="result.flags.length" class="flags">
        <span v-for="flag in result.flags" :key="flag" class="flag">{{ flag }}</span>
      </div>
    </div>

    <h2 class="section-title">Chunks ({{ result.chunk_scores.length }})</h2>

    <div
      v-for="chunk in result.chunk_scores"
      :key="chunk.chunk_ref"
      class="chunk-card"
    >
      <div class="chunk-header">
        <div class="chunk-meta">
          <code>{{ chunk.chunk_ref }}</code>
          <span class="label-tag">{{ chunk.label }}</span>
          <span v-if="chunk.page_no" class="page-tag">p.{{ chunk.page_no }}</span>
        </div>
        <div class="chunk-score-row">
          <span class="badge small" :style="{ background: bucketBg(chunk.bucket), color: bucketColor(chunk.bucket) }">
            {{ chunk.bucket }}
          </span>
          <span class="chunk-score" :style="{ color: bucketColor(chunk.bucket) }">
            {{ (chunk.chunk_score * 100).toFixed(1) }}%
          </span>
        </div>
      </div>

      <p class="chunk-preview">{{ chunk.text_preview || '(vide)' }}</p>

      <div class="heuristics">
        <div
          v-for="(h, name) in chunk.scores"
          :key="name"
          class="heuristic"
        >
          <div class="h-label">
            <span>{{ name }}</span>
            <span class="h-value">{{ (h.score * 100).toFixed(0) }}%</span>
          </div>
          <div class="h-bar-track">
            <div
              class="h-bar-fill"
              :style="{
                width: scoreBarWidth(h.score),
                background: h.score >= 0.75 ? 'var(--good)' : h.score >= 0.4 ? 'var(--uncertain)' : 'var(--bad)'
              }"
            ></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.header {
  margin-bottom: 2rem;
}
h1 {
  font-size: 1.5rem;
  font-weight: 600;
}
.subtitle {
  color: var(--text-dim);
  font-size: 0.9rem;
  margin-top: 0.25rem;
}

.input-section {
  margin-bottom: 2rem;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}
.mode-switch {
  display: flex;
  gap: 0;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}
.mode-btn {
  padding: 0.4rem 1rem;
  background: var(--surface);
  color: var(--text-dim);
  border: none;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.15s;
}
.mode-btn.active {
  background: var(--accent);
  color: white;
}
.sample-btn {
  padding: 0.4rem 0.8rem;
  background: var(--surface);
  color: var(--text-dim);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.15s;
}
.sample-btn:hover {
  background: var(--surface-hover);
  color: var(--text);
}

.editor {
  width: 100%;
  min-height: 280px;
  padding: 1rem;
  background: var(--surface);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-family: var(--mono);
  font-size: 0.82rem;
  line-height: 1.5;
  resize: vertical;
  outline: none;
  transition: border-color 0.15s;
}
.editor:focus {
  border-color: var(--accent);
}

.settings-panel {
  margin-top: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}
.setting {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.setting-label {
  font-size: 0.82rem;
  font-family: var(--mono);
  color: var(--text-dim);
}
.setting-control {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}
.setting-control input[type="range"] {
  width: 120px;
  accent-color: var(--accent);
}
.setting-value {
  font-family: var(--mono);
  font-weight: 600;
  font-size: 0.85rem;
  min-width: 1.5rem;
  text-align: right;
}

.validate-btn {
  margin-top: 0.75rem;
  width: 100%;
  padding: 0.7rem;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius);
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}
.validate-btn:hover:not(:disabled) {
  background: var(--accent-dim);
}
.validate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner {
  display: inline-block;
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.error-msg {
  margin-top: 0.75rem;
  padding: 0.6rem 1rem;
  background: var(--bad-bg);
  color: var(--bad);
  border-radius: var(--radius);
  font-size: 0.85rem;
}

.results {
  margin-top: 1rem;
}
.overall-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid;
  border-radius: var(--radius);
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}
.overall-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}
.doc-name {
  font-weight: 600;
  margin-right: 0.75rem;
}
.overall-score {
  font-size: 1.8rem;
  font-weight: 700;
  font-family: var(--mono);
}

.badge {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.05em;
}
.badge.small {
  font-size: 0.7rem;
  padding: 0.15rem 0.5rem;
}

.score-bar-track {
  height: 6px;
  background: var(--border);
  border-radius: 3px;
  overflow: hidden;
}
.score-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.4s ease;
}

.flags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.75rem;
}
.flag {
  padding: 0.25rem 0.6rem;
  background: var(--uncertain-bg);
  color: var(--uncertain);
  border-radius: var(--radius);
  font-size: 0.78rem;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  color: var(--text-dim);
}

.chunk-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem;
  margin-bottom: 0.6rem;
}
.chunk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}
.chunk-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.chunk-meta code {
  font-family: var(--mono);
  font-size: 0.75rem;
  color: var(--text-dim);
  background: none;
  padding: 0;
}
.label-tag, .page-tag {
  font-size: 0.72rem;
  padding: 0.1rem 0.4rem;
  background: var(--border);
  border-radius: 4px;
  color: var(--text-dim);
}
.chunk-score-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.chunk-score {
  font-family: var(--mono);
  font-weight: 600;
  font-size: 0.95rem;
}

.chunk-preview {
  font-size: 0.82rem;
  color: var(--text-dim);
  font-style: italic;
  margin-bottom: 0.75rem;
  word-break: break-word;
}

.heuristics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}
.heuristic {
  padding: 0.4rem 0;
}
.h-label {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  margin-bottom: 0.2rem;
}
.h-label span:first-child {
  color: var(--text-dim);
  font-family: var(--mono);
}
.h-value {
  font-weight: 600;
  font-family: var(--mono);
}
.h-bar-track {
  height: 4px;
  background: var(--border);
  border-radius: 2px;
  overflow: hidden;
}
.h-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}
</style>
