<template>
  <Card>
    <template #title>Admin Console</template>
    <template #content>
      <div class="stack-md">
        <div class="console-header">
          <Button label="Close" outlined severity="secondary" @click="emit('close')" />
        </div>

        <TabView>
          <TabPanel header="Users">
            <div class="stack-md">
              <div class="console-header">
                <Button label="New User" icon="pi pi-plus" @click="openCreateUser" />
              </div>
              <DataTable :value="users" :loading="loadingUsers" responsive-layout="scroll">
                <Column field="user_id" header="User ID" />
                <Column field="display_name" header="Name" />
                <Column field="role" header="Role" />
                <Column header="Active">
                  <template #body="slotProps">
                    <Tag :value="slotProps.data.is_active ? 'Yes' : 'No'" :severity="slotProps.data.is_active ? 'success' : 'danger'" />
                  </template>
                </Column>
                <Column header="Actions">
                  <template #body="slotProps">
                    <div class="actions-inline">
                      <Button icon="pi pi-pencil" text @click="openEditUser(slotProps.data)" />
                      <Button icon="pi pi-ban" text severity="danger" @click="deactivateUser(slotProps.data)" />
                    </div>
                  </template>
                </Column>
              </DataTable>
            </div>
          </TabPanel>

          <TabPanel header="Documents">
            <DataTable :value="documents" :loading="loadingDocs" responsive-layout="scroll">
              <Column field="filename" header="File" />
              <Column field="uploaded_by" header="Owner" />
              <Column header="Approved">
                <template #body="slotProps">
                  <Tag :value="slotProps.data.approved ? 'Yes' : 'No'" :severity="slotProps.data.approved ? 'success' : 'warning'" />
                </template>
              </Column>
              <Column header="Active">
                <template #body="slotProps">
                  <Tag :value="slotProps.data.is_active ? 'Yes' : 'No'" :severity="slotProps.data.is_active ? 'success' : 'danger'" />
                </template>
              </Column>
              <Column header="Actions">
                <template #body="slotProps">
                  <div class="actions-inline">
                    <Button icon="pi pi-pencil" text @click="openEditDocument(slotProps.data)" />
                    <Button icon="pi pi-trash" text severity="danger" @click="deleteDocument(slotProps.data.id)" />
                  </div>
                </template>
              </Column>
            </DataTable>
          </TabPanel>
        </TabView>
      </div>
    </template>
  </Card>

  <Dialog v-model:visible="showUserDialog" :header="editingUser ? 'Edit User' : 'Create User'" modal @hide="resetUserForm">
    <div class="stack-md dialog-body">
      <InputText v-model="userForm.user_id" :disabled="Boolean(editingUser)" placeholder="User ID" />
      <InputText v-model="userForm.display_name" placeholder="Display name" />
      <Dropdown v-model="userForm.role" :options="roleOptions" option-label="label" option-value="value" placeholder="Role" />
      <Dropdown v-model="userForm.is_active" :options="activeOptions" option-label="label" option-value="value" placeholder="Active" />
      <Password v-model="userForm.password" :feedback="false" toggle-mask :placeholder="editingUser ? 'New password (optional)' : 'Password'" />
      <Button :label="editingUser ? 'Save User' : 'Create User'" @click="saveUser" />
    </div>
  </Dialog>

  <Dialog v-model:visible="showDocumentDialog" header="Edit Document" modal @hide="resetDocumentForm">
    <div class="stack-md dialog-body">
      <InputText v-model="documentForm.filename" disabled />
      <MultiSelect
        v-model="documentForm.allowed_roles"
        :options="roleOptions"
        option-label="label"
        option-value="value"
        display="chip"
      />
      <Dropdown v-model="documentForm.approved" :options="activeOptions" option-label="label" option-value="value" placeholder="Approved" />
      <Dropdown v-model="documentForm.is_active" :options="activeOptions" option-label="label" option-value="value" placeholder="Active" />
      <Button label="Save Document" @click="saveDocument" />
    </div>
  </Dialog>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import MultiSelect from 'primevue/multiselect'
import Password from 'primevue/password'
import TabPanel from 'primevue/tabpanel'
import TabView from 'primevue/tabview'
import Tag from 'primevue/tag'

import { apiClient } from '../api'

const emit = defineEmits(['close', 'documents-updated'])
const toast = useToast()

const users = ref([])
const documents = ref([])
const loadingUsers = ref(false)
const loadingDocs = ref(false)
const showUserDialog = ref(false)
const showDocumentDialog = ref(false)
const editingUser = ref(null)
const editingDocument = ref(null)

const roleOptions = [
  { label: 'Employee', value: 'employee' },
  { label: 'Manager', value: 'manager' },
  { label: 'HR', value: 'hr' },
  { label: 'Admin', value: 'admin' },
]

const activeOptions = [
  { label: 'No', value: 0 },
  { label: 'Yes', value: 1 },
]

const userForm = ref({
  user_id: '',
  display_name: '',
  role: 'employee',
  is_active: 1,
  password: '',
})

const documentForm = ref({
  id: '',
  filename: '',
  allowed_roles: ['employee'],
  approved: 0,
  is_active: 1,
})

function resetUserForm() {
  editingUser.value = null
  userForm.value = {
    user_id: '',
    display_name: '',
    role: 'employee',
    is_active: 1,
    password: '',
  }
}

function resetDocumentForm() {
  editingDocument.value = null
  documentForm.value = {
    id: '',
    filename: '',
    allowed_roles: ['employee'],
    approved: 0,
    is_active: 1,
  }
}

async function loadUsers() {
  loadingUsers.value = true
  try {
    users.value = await apiClient.get('/api/admin/users')
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Users failed', detail: error.message, life: 4000 })
  } finally {
    loadingUsers.value = false
  }
}

async function loadDocuments() {
  loadingDocs.value = true
  try {
    documents.value = await apiClient.get('/api/admin/docs')
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Documents failed', detail: error.message, life: 4000 })
  } finally {
    loadingDocs.value = false
  }
}

function openCreateUser() {
  resetUserForm()
  showUserDialog.value = true
}

function openEditUser(user) {
  editingUser.value = user
  userForm.value = {
    user_id: user.user_id,
    display_name: user.display_name,
    role: user.role,
    is_active: user.is_active,
    password: '',
  }
  showUserDialog.value = true
}

async function saveUser() {
  try {
    if (editingUser.value) {
      const payload = {
        display_name: userForm.value.display_name,
        role: userForm.value.role,
        is_active: userForm.value.is_active,
      }
      if (userForm.value.password) {
        payload.password = userForm.value.password
      }
      await apiClient.patch(`/api/admin/users/${editingUser.value.user_id}`, payload)
      toast.add({ severity: 'success', summary: 'User updated', detail: 'User changes saved.', life: 3000 })
    } else {
      await apiClient.post('/api/admin/users', userForm.value)
      toast.add({ severity: 'success', summary: 'User created', detail: 'New user created.', life: 3000 })
    }
    showUserDialog.value = false
    resetUserForm()
    await loadUsers()
  } catch (error) {
    toast.add({ severity: 'error', summary: 'User save failed', detail: error.message, life: 4000 })
  }
}

async function deactivateUser(user) {
  if (!window.confirm(`Deactivate ${user.user_id}?`)) {
    return
  }
  try {
    await apiClient.patch(`/api/admin/users/${user.user_id}`, { is_active: 0 })
    await loadUsers()
    toast.add({ severity: 'success', summary: 'User updated', detail: 'User deactivated.', life: 3000 })
  } catch (error) {
    toast.add({ severity: 'error', summary: 'User update failed', detail: error.message, life: 4000 })
  }
}

function openEditDocument(document) {
  editingDocument.value = document
  documentForm.value = {
    id: document.id,
    filename: document.filename,
    allowed_roles: [...document.allowed_roles],
    approved: document.approved,
    is_active: document.is_active,
  }
  showDocumentDialog.value = true
}

async function saveDocument() {
  try {
    await apiClient.patch(`/api/admin/docs/${documentForm.value.id}`, {
      allowed_roles: documentForm.value.allowed_roles,
      approved: documentForm.value.approved,
      is_active: documentForm.value.is_active,
    })
    showDocumentDialog.value = false
    resetDocumentForm()
    await loadDocuments()
    emit('documents-updated')
    toast.add({ severity: 'success', summary: 'Document updated', detail: 'Document changes saved.', life: 3000 })
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Document save failed', detail: error.message, life: 4000 })
  }
}

async function deleteDocument(docId) {
  if (!window.confirm('Delete this document permanently?')) {
    return
  }
  try {
    await apiClient.delete(`/api/admin/docs/${docId}`)
    await loadDocuments()
    emit('documents-updated')
    toast.add({ severity: 'success', summary: 'Document deleted', detail: 'Document removed.', life: 3000 })
  } catch (error) {
    toast.add({ severity: 'error', summary: 'Document delete failed', detail: error.message, life: 4000 })
  }
}

onMounted(async () => {
  await Promise.all([loadUsers(), loadDocuments()])
})
</script>

<style scoped>
.stack-md {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.console-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.actions-inline {
  display: flex;
  gap: 6px;
}

.dialog-body {
  min-width: min(520px, 80vw);
}
</style>
