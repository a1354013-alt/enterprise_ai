export function createInitialUser() {
  return {
    user_id: '',
    role: '',
    display_name: '',
  }
}

export function createInitialUiState() {
  return {
    activeSection: 'knowledge',
    documents: [],
    photos: [],
    knowledge: {
      question: '',
      answer: '',
      sources: [],
      recentEntries: [],
    },
    logbook: {
      entries: [],
    },
    docsPhotos: {
      selectedDocFile: null,
      docTags: '',
      docCategory: '',
      selectedPhotoFile: null,
      photoTags: '',
      photoDescription: '',
    },
    autoTest: {
      runs: [],
      selectedRun: null,
    },
    settings: {
      showAdminConsole: false,
    },
  }
}

