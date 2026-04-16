<template>
  <div class="grid">
    <Card>
      <template #title>Documents</template>
      <template #subtitle>Upload and tag engineering docs. Indexing happens immediately for your workspace.</template>
      <template #content>
        <div class="stack-md">
          <div class="row">
            <input ref="docInput" type="file" accept=".pdf,.txt,.md" class="hidden-input" @change="onDocSelected" />
            <Button label="Choose Document" icon="pi pi-upload" outlined @click="openDocPicker" />
            <span v-if="selectedDoc" class="muted">{{ selectedDoc.name }}</span>
          </div>

          <InputText v-model="docCategory" placeholder="Category (optional)" />
          <InputText v-model="docTags" placeholder="Tags (comma separated, optional)" />
          <div class="row">
            <Button label="Upload" :loading="uploadingDoc" @click="uploadDoc" />
            <Button label="Refresh" outlined icon="pi pi-refresh" :loading="loadingDocs" @click="loadDocuments" />
          </div>

          <InputText v-model="docFilterText" placeholder="Filter docs (filename/tags)" />

          <DataTable :value="filteredDocuments" :loading="loadingDocs" data-key="id" size="small" responsive-layout="scroll">
            <Column field="filename" header="File" />
            <Column field="category" header="Category" />
            <Column field="tags" header="Tags" />
            <Column field="status" header="Status" />
            <Column header="Actions">
              <template #body="slotProps">
                <div class="actions-inline">
                  <Button icon="pi pi-eye" text severity="secondary" @click="previewDocument(slotProps.data)" />
                  <Button icon="pi pi-download" text severity="secondary" @click="downloadDocument(slotProps.data)" />
                  <Button icon="pi pi-pencil" text severity="secondary" @click="openDocEditor(slotProps.data)" />
                  <Button icon="pi pi-sitemap" text severity="secondary" @click="showDocReferences(slotProps.data)" />
                  <Button icon="pi pi-archive" text severity="secondary" @click="archiveDocument(slotProps.data)" />
                  <Button icon="pi pi-trash" text severity="danger" @click="deleteDocument(slotProps.data)" />
                </div>
              </template>
            </Column>
          </DataTable>

          <RelatedItemsPanel v-if="selectedRelatedItemId" :item-id="selectedRelatedItemId" />
        </div>
      </template>
    </Card>

    <Card>
      <template #title>Photos / Images</template>
      <template #subtitle>Upload images, add tags/description. OCR is optional and safe-by-default.</template>
      <template #content>
        <div class="stack-md">
          <div class="row">
            <input ref="photoInput" type="file" accept="image/*" class="hidden-input" @change="onPhotoSelected" />
            <Button label="Choose Image" icon="pi pi-image" outlined @click="openPhotoPicker" />
            <span v-if="selectedPhoto" class="muted">{{ selectedPhoto.name }}</span>
          </div>

          <InputText v-model="photoTags" placeholder="Tags (comma separated, optional)" />
          <Textarea v-model="photoDescription" rows="2" placeholder="Description (optional)" />
          <div class="row">
            <Button label="Upload" :loading="uploadingPhoto" @click="uploadPhoto" />
            <Button label="Refresh" outlined icon="pi pi-refresh" :loading="loadingPhotos" @click="loadPhotos" />
          </div>

          <DataTable :value="photos" :loading="loadingPhotos" data-key="id" size="small" responsive-layout="scroll">
            <Column field="filename" header="File" />
            <Column field="tags" header="Tags" />
            <Column field="description" header="Description" />
            <Column field="created_at" header="Created" />
            <Column header="Actions">
              <template #body="slotProps">
                <div class="actions-inline">
                  <Button icon="pi pi-eye" text severity="secondary" @click="previewPhoto(slotProps.data)" />
                  <Button icon="pi pi-download" text severity="secondary" @click="downloadPhoto(slotProps.data)" />
                  <Button icon="pi pi-pencil" text severity="secondary" @click="openPhotoEditor(slotProps.data)" />
                  <Button icon="pi pi-sitemap" text severity="secondary" @click="showPhotoReferences(slotProps.data)" />
                  <Button icon="pi pi-trash" text severity="danger" @click="deletePhoto(slotProps.data)" />
                </div>
              </template>
            </Column>
          </DataTable>
        </div>
      </template>
    </Card>
  </div>

  <Dialog v-model:visible="docEditorVisible" modal header="Edit document" :style="{ width: 'min(720px, 95vw)' }">
    <div class="stack-md">
      <div class="muted"><code>{{ docEditor.id ? `document:${docEditor.id}` : '' }}</code></div>
      <InputText v-model="docEditor.category" placeholder="Category" />
      <InputText v-model="docEditor.tags" placeholder="Tags" />
      <Dropdown v-model="docEditor.status" :options="statusOptions" option-label="label" option-value="value" placeholder="Status" />
      <div class="row">
        <Button label="Save" icon="pi pi-save" :loading="docEditorSaving" @click="saveDocEditor" />
        <Button label="Close" outlined severity="secondary" :disabled="docEditorSaving" @click="docEditorVisible = false" />
      </div>
    </div>
  </Dialog>

  <Dialog v-model:visible="photoEditorVisible" modal header="Edit photo" :style="{ width: 'min(720px, 95vw)' }">
    <div class="stack-md">
      <div class="muted"><code>{{ photoEditor.id ? `photo:${photoEditor.id}` : '' }}</code></div>
      <InputText v-model="photoEditor.tags" placeholder="Tags" />
      <Textarea v-model="photoEditor.description" rows="2" placeholder="Description" />
      <Dropdown v-model="photoEditor.status" :options="statusOptions" option-label="label" option-value="value" placeholder="Status" />
      <div class="row">
        <Button label="Save" icon="pi pi-save" :loading="photoEditorSaving" @click="savePhotoEditor" />
        <Button label="Close" outlined severity="secondary" :disabled="photoEditorSaving" @click="photoEditorVisible = false" />
      </div>
    </div>
  </Dialog>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'

import { apiClient } from '../api'
import { downloadBlob, openBlobInNewTab } from '../utils/blob'
import RelatedItemsPanel from './RelatedItemsPanel.vue'

const toast = useToast()

const docInput = ref(null)
const photoInput = ref(null)

const documents = ref([])
const photos = ref([])
const docFilterText = ref('')

const selectedDoc = ref(null)
const uploadingDoc = ref(false)
const loadingDocs = ref(false)
const docCategory = ref('')
const docTags = ref('')

const selectedPhoto = ref(null)
const uploadingPhoto = ref(false)
const loadingPhotos = ref(false)
const photoTags = ref('')
const photoDescription = ref('')

const selectedRelatedItemId = ref('')

const docEditorVisible = ref(false)
const docEditorSaving = ref(false)
const docEditor = ref({ id: '', category: '', tags: '', status: 'reviewed' })

const photoEditorVisible = ref(false)
const photoEditorSaving = ref(false)
const photoEditor = ref({ id: '', tags: '', description: '', status: 'reviewed' })

const statusOptions = [
  { label: 'Draft', value: 'draft' },
  { label: 'Reviewed', value: 'reviewed' },
  { label: 'Verified', value: 'verified' },
  { label: 'Archived', value: 'archived' },
]

const filteredDocuments = computed(() => {
  const query = String(docFilterText.value || '').trim().toLowerCase()
  if (!query) {
    return documents.value
  }
  return documents.value.filter((doc) => {
    const haystack = `${doc.filename || ''} ${doc.category || ''} ${doc.tags || ''}`.toLowerCase()
    return haystack.includes(query)
  })
})

function openDocPicker() {
  docInput.value?.click()
}

function openPhotoPicker() {
  photoInput.value?.click()
}

function onDocSelected(event) {
  selectedDoc.value = event.target.files?.[0] || null
}

function onPhotoSelected(event) {
  selectedPhoto.value = event.target.files?.[0] || null
}

async function loadDocuments() {
  loadingDocs.value = true
  try {
    documents.value = await apiClient.get('/api/docs')
  } catch (error) {
    documents.value = []
  } finally {
    loadingDocs.value = false
  }
}

async function uploadDoc() {
  if (!selectedDoc.value) {
    toast.add({ severity: 'warn', summary: 'No file selected', detail: 'Choose a document to upload.', life: 3000 })
    return
  }

  uploadingDoc.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedDoc.value)
    formData.append('category', docCategory.value || '')
    formData.append('tags', docTags.value || '')
    await apiClient.post('/api/docs/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    toast.add({ severity: 'success', summary: 'Uploaded', detail: 'Document uploaded.', life: 3000 })
    selectedDoc.value = null
    if (docInput.value) {
      docInput.value.value = ''
    }
    docCategory.value = ''
    docTags.value = ''
    await loadDocuments()
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Upload failed', detail: error.message, life: 4000 })
  } finally {
    uploadingDoc.value = false
  }
}

async function loadPhotos() {
  loadingPhotos.value = true
  try {
    photos.value = await apiClient.get('/api/photos')
  } catch (error) {
    photos.value = []
  } finally {
    loadingPhotos.value = false
  }
}

async function uploadPhoto() {
  if (!selectedPhoto.value) {
    toast.add({ severity: 'warn', summary: 'No file selected', detail: 'Choose an image to upload.', life: 3000 })
    return
  }

  uploadingPhoto.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedPhoto.value)
    formData.append('tags', photoTags.value || '')
    formData.append('description', photoDescription.value || '')
    await apiClient.post('/api/photos/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    toast.add({ severity: 'success', summary: 'Uploaded', detail: 'Image saved.', life: 3000 })
    selectedPhoto.value = null
    if (photoInput.value) {
      photoInput.value.value = ''
    }
    photoTags.value = ''
    photoDescription.value = ''
    await loadPhotos()
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Upload failed', detail: error.message, life: 4000 })
  } finally {
    uploadingPhoto.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadDocuments(), loadPhotos()])
})

function showDocReferences(doc) {
  if (!doc?.id) {
    return
  }
  selectedRelatedItemId.value = `document:${doc.id}`
}

function showPhotoReferences(photo) {
  if (!photo?.id) {
    return
  }
  selectedRelatedItemId.value = `photo:${photo.id}`
}

async function previewDocument(doc) {
  if (!doc?.id) {
    return
  }
  try {
    const blob = await apiClient.get(`/api/docs/${doc.id}/download`, { params: { inline: 1 }, responseType: 'blob' })
    openBlobInNewTab(blob)
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Preview failed', detail: error.message, life: 4000 })
  }
}

async function downloadDocument(doc) {
  if (!doc?.id) {
    return
  }
  try {
    const blob = await apiClient.get(`/api/docs/${doc.id}/download`, { responseType: 'blob' })
    downloadBlob(blob, doc.filename || `document-${doc.id}`)
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Download failed', detail: error.message, life: 4000 })
  }
}

function openDocEditor(doc) {
  if (!doc?.id) {
    return
  }
  docEditor.value = {
    id: doc.id,
    category: doc.category || '',
    tags: doc.tags || '',
    status: doc.status || 'reviewed',
  }
  docEditorVisible.value = true
}

async function saveDocEditor() {
  if (!docEditor.value?.id) {
    return
  }
  docEditorSaving.value = true
  try {
    await apiClient.patch(`/api/docs/${docEditor.value.id}`, {
      category: String(docEditor.value.category || ''),
      tags: String(docEditor.value.tags || ''),
      status: docEditor.value.status || 'reviewed',
    })
    toast.add({ severity: 'success', summary: 'Saved', detail: 'Document updated.', life: 2500 })
    docEditorVisible.value = false
    await loadDocuments()
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Save failed', detail: error.message, life: 4000 })
  } finally {
    docEditorSaving.value = false
  }
}

async function archiveDocument(doc) {
  if (!doc?.id) {
    return
  }
  if (!window.confirm(`Archive "${doc.filename}"?`)) {
    return
  }
  try {
    await apiClient.patch(`/api/docs/${doc.id}`, { status: 'archived' })
    toast.add({ severity: 'success', summary: 'Archived', detail: 'Document archived.', life: 2500 })
    await loadDocuments()
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Archive failed', detail: error.message, life: 4000 })
  }
}

async function deleteDocument(doc) {
  if (!doc?.id) {
    return
  }
  if (!window.confirm(`Delete "${doc.filename}"?`)) {
    return
  }
  try {
    await apiClient.delete(`/api/docs/${doc.id}`)
    toast.add({ severity: 'success', summary: 'Deleted', detail: 'Document deleted.', life: 2500 })
    await loadDocuments()
    if (selectedRelatedItemId.value === `document:${doc.id}`) {
      selectedRelatedItemId.value = ''
    }
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Delete failed', detail: error.message, life: 4000 })
  }
}

async function previewPhoto(photo) {
  if (!photo?.id) {
    return
  }
  try {
    const blob = await apiClient.get(`/api/photos/${photo.id}/download`, { params: { inline: 1 }, responseType: 'blob' })
    openBlobInNewTab(blob)
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Preview failed', detail: error.message, life: 4000 })
  }
}

async function downloadPhoto(photo) {
  if (!photo?.id) {
    return
  }
  try {
    const blob = await apiClient.get(`/api/photos/${photo.id}/download`, { responseType: 'blob' })
    downloadBlob(blob, photo.filename || `photo-${photo.id}`)
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Download failed', detail: error.message, life: 4000 })
  }
}

function openPhotoEditor(photo) {
  if (!photo?.id) {
    return
  }
  photoEditor.value = {
    id: photo.id,
    tags: photo.tags || '',
    description: photo.description || '',
    status: photo.status || 'reviewed',
  }
  photoEditorVisible.value = true
}

async function savePhotoEditor() {
  if (!photoEditor.value?.id) {
    return
  }
  photoEditorSaving.value = true
  try {
    await apiClient.patch(`/api/photos/${photoEditor.value.id}`, {
      tags: String(photoEditor.value.tags || ''),
      description: String(photoEditor.value.description || ''),
      status: photoEditor.value.status || 'reviewed',
    })
    toast.add({ severity: 'success', summary: 'Saved', detail: 'Photo updated.', life: 2500 })
    photoEditorVisible.value = false
    await loadPhotos()
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Save failed', detail: error.message, life: 4000 })
  } finally {
    photoEditorSaving.value = false
  }
}

async function deletePhoto(photo) {
  if (!photo?.id) {
    return
  }
  if (!window.confirm(`Delete "${photo.filename}"?`)) {
    return
  }
  try {
    await apiClient.delete(`/api/photos/${photo.id}`)
    toast.add({ severity: 'success', summary: 'Deleted', detail: 'Photo deleted.', life: 2500 })
    await loadPhotos()
    if (selectedRelatedItemId.value === `photo:${photo.id}`) {
      selectedRelatedItemId.value = ''
    }
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Delete failed', detail: error.message, life: 4000 })
  }
}
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

.row {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.hidden-input {
  display: none;
}

.muted {
  color: #51606f;
  font-size: 13px;
}

.actions-inline {
  display: flex;
  gap: 6px;
}

@media (max-width: 1080px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
