<template>
  <div class="grid">
    <Card>
      <template #title>Recent activity</template>
      <template #subtitle>A traceable timeline across knowledge, logbook, documents, photos, prompts, and AutoTest runs.</template>
      <template #content>
        <div class="stack-md">
          <div class="row">
            <Button label="Refresh" outlined icon="pi pi-refresh" :loading="loading" @click="load" />
            <InputText v-model="filterText" placeholder="Filter (title/type/status/source)" class="filter" />
          </div>

          <DataTable
            :value="filtered"
            :loading="loading"
            data-key="item_id"
            size="small"
            responsive-layout="scroll"
            @row-click="onRowClick"
          >
            <Column field="kind" header="Type" />
            <Column field="title" header="Title" />
            <Column field="status" header="Status" />
            <Column field="source" header="Source" />
            <Column field="when" header="When" />
            <Column header="Item">
              <template #body="slotProps">
                <code>{{ slotProps.data.item_id }}</code>
              </template>
            </Column>
          </DataTable>

          <RelatedItemsPanel v-if="selectedItemId" :item-id="selectedItemId" />
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import InputText from 'primevue/inputtext'

import { apiClient } from '../api'
import RelatedItemsPanel from './RelatedItemsPanel.vue'

const loading = ref(false)
const filterText = ref('')
const items = ref([])
const selectedItemId = ref('')

const filtered = computed(() => {
  const query = String(filterText.value || '').trim().toLowerCase()
  if (!query) {
    return items.value
  }
  return items.value.filter((item) => {
    const haystack = `${item.kind} ${item.title} ${item.status} ${item.source} ${item.item_id}`.toLowerCase()
    return haystack.includes(query)
  })
})

function normalizeWhen(value) {
  return String(value || '').replace('T', ' ').replace('Z', '')
}

function byWhenDesc(a, b) {
  return String(b.when || '').localeCompare(String(a.when || ''))
}

async function load() {
  loading.value = true
  try {
    const [knowledge, logbook, docs, photos, runs, prompts] = await Promise.all([
      apiClient.get('/api/knowledge/entries'),
      apiClient.get('/api/logbook/entries'),
      apiClient.get('/api/docs'),
      apiClient.get('/api/photos'),
      apiClient.get('/api/autotest/runs'),
      apiClient.get('/api/prompts'),
    ])

    const mapped = []

    for (const entry of knowledge || []) {
      mapped.push({
        kind: 'Knowledge',
        title: entry.title || entry.problem?.slice?.(0, 80) || 'Knowledge entry',
        status: entry.status || '',
        source: `${entry.source_type || ''}`.trim(),
        when: normalizeWhen(entry.updated_at || entry.created_at),
        item_id: `knowledge:${entry.id}`,
      })
    }
    for (const entry of logbook || []) {
      mapped.push({
        kind: 'Logbook',
        title: entry.title || entry.problem?.slice?.(0, 80) || 'Logbook entry',
        status: entry.status || '',
        source: `${entry.source_type || ''}`.trim(),
        when: normalizeWhen(entry.updated_at || entry.created_at),
        item_id: `logbook:${entry.id}`,
      })
    }
    for (const doc of docs || []) {
      mapped.push({
        kind: 'Document',
        title: doc.filename || 'Document',
        status: doc.status || '',
        source: 'upload',
        when: normalizeWhen(doc.updated_at || doc.uploaded_at),
        item_id: `document:${doc.id}`,
      })
    }
    for (const photo of photos || []) {
      mapped.push({
        kind: 'Photo',
        title: photo.filename || 'Photo',
        status: photo.status || '',
        source: 'upload',
        when: normalizeWhen(photo.updated_at || photo.created_at),
        item_id: `photo:${photo.id}`,
      })
    }
    for (const run of runs || []) {
      mapped.push({
        kind: 'AutoTest',
        title: run.project_name || run.id,
        status: run.status || '',
        source: 'upload',
        when: normalizeWhen(run.created_at),
        item_id: `autotest_run:${run.id}`,
      })
    }
    for (const prompt of prompts || []) {
      mapped.push({
        kind: 'Prompt',
        title: prompt.title || 'Prompt',
        status: 'active',
        source: 'manual',
        when: normalizeWhen(prompt.updated_at || prompt.created_at),
        item_id: `prompt:${prompt.id}`,
      })
    }

    items.value = mapped.sort(byWhenDesc)
  } finally {
    loading.value = false
  }
}

function onRowClick(event) {
  const item = event?.data
  if (!item?.item_id) {
    return
  }
  selectedItemId.value = item.item_id
}

onMounted(load)
</script>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.stack-md {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.row {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.filter {
  min-width: min(520px, 100%);
}
</style>

