export function createInitialUser() {
  return {
    user_id: '',
    role: '',
    display_name: '',
  }
}

export function createInitialUiState() {
  return {
    showAdminConsole: false,
    documents: [],
    selectedFile: null,
    uploadRoles: ['employee'],
    qaQuestion: '',
    qaAnswer: '',
    qaSources: [],
    selectedTemplate: '',
    formInputs: {},
    generatedContent: '',
    templates: [],
  }
}
