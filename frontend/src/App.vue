<template>
  <div class="app-shell">
    <Toast />

    <section v-if="!isLoggedIn" class="login-shell">
      <Card class="login-card">
        <template #title>Enterprise AI Assistant</template>
        <template #subtitle>Secure knowledge search, document access, and admin workflow.</template>
        <template #content>
          <div class="stack-md">
            <label class="field-label" for="userId">User ID</label>
            <InputText id="userId" v-model="loginForm.user_id" autocomplete="username" />

            <label class="field-label" for="password">Password</label>
            <Password id="password" v-model="loginForm.password" :feedback="false" toggle-mask input-class="w-full" />

            <Button label="Sign In" :loading="loginLoading" @click="login" />
          </div>
        </template>
      </Card>
    </section>

    <section v-else class="workspace-shell">
      <header class="topbar">
        <div>
          <h1>Enterprise AI Assistant</h1>
          <p>{{ currentUser.display_name }} ({{ currentUser.role }})</p>
        </div>
        <div class="toolbar-actions">
          <Button
            v-if="currentUser.role === 'admin'"
            :label="showAdminConsole ? 'Back To Workspace' : 'Open Admin Console'"
            severity="contrast"
            outlined
            @click="showAdminConsole = !showAdminConsole"
          />
          <Button label="Logout" severity="secondary" @click="logout()" />
        </div>
      </header>

      <AdminConsole
        v-if="showAdminConsole && currentUser.role === 'admin'"
        @close="closeAdminConsole"
        @documents-updated="loadDocuments"
      />

      <main v-else class="main-grid">
        <Card>
          <template #title>Documents</template>
          <template #content>
            <div class="stack-md">
              <input ref="fileInput" type="file" accept=".pdf,.txt,.md" class="hidden-input" @change="onFileSelected" />
              <Button label="Choose File" icon="pi pi-upload" outlined @click="openFilePicker" />
              <p v-if="selectedFile" class="muted-text">{{ selectedFile.name }}</p>
              <MultiSelect
                v-model="uploadRoles"
                :options="roleOptions"
                option-label="label"
                option-value="value"
                display="chip"
                placeholder="Allowed roles"
              />
              <Button label="Upload Document" :loading="uploadLoading" @click="uploadFile" />

              <DataTable :value="documents" size="small" data-key="id" responsive-layout="scroll">
                <Column field="filename" header="File" />
                <Column field="uploaded_by" header="Owner" />
                <Column header="Status">
                  <template #body="slotProps">
                    <Tag :value="slotProps.data.approved ? 'Approved' : 'Pending'" :severity="slotProps.data.approved ? 'success' : 'warning'" />
                  </template>
                </Column>
                <Column header="Actions">
                  <template #body="slotProps">
                    <Button
                      v-if="canDeleteDocument(slotProps.data)"
                      icon="pi pi-trash"
                      text
                      severity="danger"
                      @click="deleteDocument(slotProps.data.id)"
                    />
                  </template>
                </Column>
              </DataTable>
            </div>
          </template>
        </Card>

        <Card>
          <template #title>Document QA</template>
          <template #content>
            <div class="stack-md">
              <Textarea v-model="qaQuestion" rows="5" placeholder="Ask a question using approved documents." />
              <Button label="Ask" icon="pi pi-send" :loading="qaLoading" @click="submitQA" />
              <div v-if="qaAnswer" class="result-box">
                <h3>Answer</h3>
                <p>{{ qaAnswer }}</p>
                <div v-if="qaSources.length" class="stack-sm">
                  <h4>Sources</h4>
                  <article v-for="(source, index) in qaSources" :key="index" class="source-card">
                    <strong>{{ source.doc_name }} · {{ source.page_or_section }}</strong>
                    <p>{{ source.chunk_text }}</p>
                  </article>
                </div>
              </div>
            </div>
          </template>
        </Card>

        <Card>
          <template #title>Template Generator</template>
          <template #content>
            <div class="stack-md">
              <Dropdown
                v-model="selectedTemplate"
                :options="templates"
                option-label="label"
                option-value="value"
                placeholder="Choose a template"
                @change="onTemplateChange"
              />
              <div v-for="field in templateFields" :key="field" class="stack-sm">
                <label class="field-label">{{ formatFieldLabel(field) }}</label>
                <Textarea v-model="formInputs[field]" rows="3" />
              </div>
              <Button label="Generate" :disabled="!isFormValid" :loading="generateLoading" @click="generateDocument" />
              <div v-if="generatedContent" class="result-box">
                <h3>Generated Content</h3>
                <pre>{{ generatedContent }}</pre>
              </div>
            </div>
          </template>
        </Card>
      </main>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import MultiSelect from 'primevue/multiselect'
import Password from 'primevue/password'
import Tag from 'primevue/tag'
import Textarea from 'primevue/textarea'
import Toast from 'primevue/toast'

import AdminConsole from './components/AdminConsole.vue'
import { createInitialUiState, createInitialUser } from './app-state'
import { apiClient } from './api'
import { clearToken, onUnauthorized, restoreToken, setToken } from './auth'

const toast = useToast()

const loginLoading = ref(false)
const uploadLoading = ref(false)
const qaLoading = ref(false)
const generateLoading = ref(false)
const currentUser = ref(createInitialUser())
const loginForm = ref({ user_id: '', password: '' })
const showAdminConsole = ref(false)
const documents = ref([])
const selectedFile = ref(null)
const uploadRoles = ref(['employee'])
const qaQuestion = ref('')
const qaAnswer = ref('')
const qaSources = ref([])
const selectedTemplate = ref('')
const templates = ref([])
const formInputs = ref({})
const generatedContent = ref('')
const fileInput = ref(null)

const roleOptions = [
  { label: 'Employee', value: 'employee' },
  { label: 'Manager', value: 'manager' },
  { label: 'HR', value: 'hr' },
  { label: 'Admin', value: 'admin' },
]

const isLoggedIn = computed(() => Boolean(currentUser.value.user_id))
const templateFields = computed(() => templates.value.find((item) => item.value === selectedTemplate.value)?.fields || [])
const isFormValid = computed(() => templateFields.value.every((field) => String(formInputs.value[field] || '').trim()))

function resetWorkspaceState() {
  const initialState = createInitialUiState()
  showAdminConsole.value = initialState.showAdminConsole
  documents.value = initialState.documents
  selectedFile.value = initialState.selectedFile
  uploadRoles.value = initialState.uploadRoles
  qaQuestion.value = initialState.qaQuestion
  qaAnswer.value = initialState.qaAnswer
  qaSources.value = initialState.qaSources
  selectedTemplate.value = initialState.selectedTemplate
  formInputs.value = initialState.formInputs
  generatedContent.value = initialState.generatedContent
  templates.value = initialState.templates
}

function formatFieldLabel(field) {
  return field.replaceAll('_', ' ').replace(/\b\w/g, (value) => value.toUpperCase())
}

function canDeleteDocument(document) {
  return currentUser.value.role === 'admin' || currentUser.value.user_id === document.uploaded_by
}

function openFilePicker() {
  fileInput.value?.click()
}

function onFileSelected(event) {
  selectedFile.value = event.target.files?.[0] || null
}

async function login() {
  if (!loginForm.value.user_id || !loginForm.value.password) {
    toast.add({ severity: 'warn', summary: 'Missing fields', detail: 'Enter user ID and password.', life: 3000 })
    return
  }

  loginLoading.value = true
  try {
    const response = await apiClient.post('/api/login', loginForm.value, { skipAuth: true })
    setToken(response.access_token)
    await bootstrapSession()
    toast.add({ severity: 'success', summary: 'Signed in', detail: 'Session restored successfully.', life: 3000 })
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Login failed', detail: error.message, life: 4000 })
    clearToken()
  } finally {
    loginLoading.value = false
  }
}

function logout(showToast = true) {
  clearToken()
  currentUser.value = createInitialUser()
  loginForm.value = { user_id: '', password: '' }
  resetWorkspaceState()
  if (fileInput.value) {
    fileInput.value.value = ''
  }
  if (showToast) {
    toast.add({ severity: 'info', summary: 'Logged out', detail: 'Session cleared.', life: 3000 })
  }
}

async function bootstrapSession() {
  const token = restoreToken()
  if (!token) {
    return
  }

  const me = await apiClient.get('/api/me')
  currentUser.value = me
  await Promise.all([loadDocuments(), loadTemplates()])
}

async function loadDocuments() {
  documents.value = await apiClient.get('/api/docs')
}

async function loadTemplates() {
  const response = await apiClient.get('/api/meta/templates')
  templates.value = response.templates
}

async function uploadFile() {
  if (!selectedFile.value) {
    toast.add({ severity: 'warn', summary: 'No file selected', detail: 'Choose a document to upload.', life: 3000 })
    return
  }

  uploadLoading.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('allowed_roles', uploadRoles.value.join(','))
    await apiClient.post('/api/docs/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    selectedFile.value = null
    if (fileInput.value) {
      fileInput.value.value = ''
    }
    uploadRoles.value = ['employee']
    await loadDocuments()
    toast.add({ severity: 'success', summary: 'Uploaded', detail: 'Document sent for admin approval.', life: 3000 })
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Upload failed', detail: error.message, life: 4000 })
  } finally {
    uploadLoading.value = false
  }
}

async function deleteDocument(docId) {
  if (!window.confirm('Delete this document?')) {
    return
  }
  try {
    await apiClient.delete(`/api/docs/${docId}`)
    await loadDocuments()
    toast.add({ severity: 'success', summary: 'Deleted', detail: 'Document removed.', life: 3000 })
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Delete failed', detail: error.message, life: 4000 })
  }
}

async function submitQA() {
  if (!qaQuestion.value.trim()) {
    toast.add({ severity: 'warn', summary: 'Question required', detail: 'Enter a question first.', life: 3000 })
    return
  }

  qaLoading.value = true
  try {
    const response = await apiClient.post('/api/qa', { question: qaQuestion.value.trim() })
    qaAnswer.value = response.answer
    qaSources.value = response.sources || []
  } catch (error) {
    toast.add({ severity: 'error', summary: 'QA failed', detail: error.message, life: 4000 })
  } finally {
    qaLoading.value = false
  }
}

function onTemplateChange() {
  formInputs.value = {}
  generatedContent.value = ''
}

async function generateDocument() {
  generateLoading.value = true
  try {
    const response = await apiClient.post('/api/generate', {
      template_type: selectedTemplate.value,
      inputs: formInputs.value,
    })
    generatedContent.value = response.content
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Generation failed', detail: error.message, life: 4000 })
  } finally {
    generateLoading.value = false
  }
}

function closeAdminConsole() {
  showAdminConsole.value = false
  loadDocuments()
}

const removeUnauthorizedListener = onUnauthorized((event) => {
  if (isLoggedIn.value) {
    toast.add({ severity: 'warn', summary: 'Session expired', detail: event.detail || 'Please sign in again.', life: 4000 })
  }
  logout(false)
})

onMounted(async () => {
  try {
    await bootstrapSession()
  } catch (error) {
    clearToken()
  }
})

onBeforeUnmount(() => {
  removeUnauthorizedListener()
})
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  padding: 24px;
  background: linear-gradient(145deg, #f4efe2 0%, #dbe9f4 100%);
}

.login-shell {
  min-height: calc(100vh - 48px);
  display: grid;
  place-items: center;
}

.login-card {
  width: min(420px, 100%);
}

.workspace-shell {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: blur(12px);
}

.topbar h1,
.topbar p {
  margin: 0;
}

.toolbar-actions {
  display: flex;
  gap: 12px;
}

.main-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
}

.stack-md {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stack-sm {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-label {
  font-weight: 600;
}

.hidden-input {
  display: none;
}

.muted-text {
  margin: 0;
  color: #51606f;
}

.result-box {
  padding: 16px;
  border-radius: 14px;
  background: #f7fafc;
}

.result-box pre {
  white-space: pre-wrap;
  margin: 0;
  font-family: inherit;
}

.source-card {
  padding: 10px 12px;
  border-radius: 12px;
  background: white;
  border: 1px solid #d8e1e8;
}

.w-full {
  width: 100%;
}

@media (max-width: 1080px) {
  .main-grid {
    grid-template-columns: 1fr;
  }

  .topbar {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
