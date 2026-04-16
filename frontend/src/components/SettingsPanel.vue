<template>
  <div class="grid">
    <Card>
      <template #title>Local AI provider</template>
      <template #subtitle>Ollama is the default provider. If it is down, the workspace keeps working in fallback mode.</template>
      <template #content>
        <div class="stack-md">
          <Button label="Refresh" outlined icon="pi pi-refresh" :loading="loading" @click="loadStatus" />
          <div class="kv">
            <div class="key">Provider</div>
            <div class="value">{{ status.provider || '-' }}</div>
            <div class="key">Model</div>
            <div class="value">{{ status.model || '-' }}</div>
            <div class="key">Base URL</div>
            <div class="value">{{ status.base_url || '-' }}</div>
            <div class="key">Healthy</div>
            <div class="value">{{ status.healthy ? 'yes' : 'no' }}</div>
            <div class="key">Fallback</div>
            <div class="value">{{ status.fallback_mode ? 'enabled' : 'disabled' }}</div>
          </div>
          <p class="muted">
            Start Ollama: `ollama serve` and pull a model: `ollama pull llama3.1`.
          </p>
        </div>
      </template>
    </Card>

    <Card>
      <template #title>Prompt templates</template>
      <template #subtitle>Engineering-focused templates for bug reports, troubleshooting notes, PR descriptions, and postmortems.</template>
      <template #content>
        <div class="stack-md">
          <Button label="Refresh" outlined icon="pi pi-refresh" :loading="loadingTemplates" @click="loadTemplates" />
          <div class="kv" v-if="templates.length">
            <div class="key">Available</div>
            <div class="value">{{ templates.map((t) => t.value).join(', ') }}</div>
          </div>
          <p class="muted">Use `Generate` in the Knowledge tab via API: `POST /api/generate` with `template_type` and `inputs`.</p>
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import Button from 'primevue/button'
import Card from 'primevue/card'

import { apiClient } from '../api'

defineProps({
  currentUser: {
    type: Object,
    default: () => ({}),
  },
})

const loading = ref(false)
const loadingTemplates = ref(false)
const status = ref({
  provider: '',
  model: '',
  base_url: '',
  healthy: false,
  fallback_mode: true,
})
const templates = ref([])

async function loadStatus() {
  loading.value = true
  try {
    status.value = await apiClient.get('/api/settings/llm')
  } catch (error) {
    status.value = { provider: 'unknown', model: '', base_url: '', healthy: false, fallback_mode: true }
  } finally {
    loading.value = false
  }
}

onMounted(loadStatus)

async function loadTemplates() {
  loadingTemplates.value = true
  try {
    const payload = await apiClient.get('/api/meta/templates')
    templates.value = payload?.templates || []
  } catch (error) {
    templates.value = []
  } finally {
    loadingTemplates.value = false
  }
}

onMounted(loadTemplates)
</script>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.stack-md {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.kv {
  display: grid;
  grid-template-columns: 110px minmax(0, 1fr);
  gap: 10px 12px;
  padding: 12px;
  border-radius: 12px;
  background: #f7fafc;
}

.key {
  font-weight: 600;
  color: #3a4755;
}

.value {
  color: #1f2d3d;
  word-break: break-word;
}

.muted {
  margin: 0;
  color: #51606f;
  font-size: 13px;
}

@media (max-width: 1080px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
