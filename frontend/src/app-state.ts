import type {
  AutoTestRunListItemResponse,
  DocumentResponse,
  KnowledgeEntryResponse,
  LogbookEntryResponse,
  MeResponse,
  PhotoResponse,
  SavedPromptResponse,
  Source,
} from './types'

export type UiSection =
  | 'activity'
  | 'search'
  | 'knowledge'
  | 'logbook'
  | 'docsPhotos'
  | 'autotest'
  | 'prompts'
  | 'generator'
  | 'settings'

export interface UiState {
  activeSection: UiSection
  documents: DocumentResponse[]
  photos: PhotoResponse[]
  knowledge: {
    question: string
    answer: string
    sources: Source[]
    recentEntries: KnowledgeEntryResponse[]
  }
  logbook: {
    entries: LogbookEntryResponse[]
  }
  docsPhotos: {
    selectedDocFile: File | null
    docTags: string
    docCategory: string
    selectedPhotoFile: File | null
    photoTags: string
    photoDescription: string
  }
  autoTest: {
    runs: AutoTestRunListItemResponse[]
    selectedRun: unknown | null
  }
  prompts?: {
    items: SavedPromptResponse[]
  }
  settings: {
    showAdminConsole: boolean
  }
}

export function createInitialUser(): MeResponse {
  return {
    user_id: '',
    role: '',
    display_name: '',
  }
}

export function createInitialUiState(): UiState {
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
