import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

import DocsPhotosPanel from '../src/components/DocsPhotosPanel.vue'
import { PrimeStubs } from './stubs'

vi.mock('primevue/usetoast', () => ({
  useToast: () => ({ add: vi.fn() }),
}))

const mocks = vi.hoisted(() => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

vi.mock('../src/api', () => ({
  apiClient: mocks.apiClient,
}))

vi.mock('../src/utils/blob', () => ({
  downloadBlob: vi.fn(),
  openBlobInNewTab: vi.fn(),
}))

describe('DocsPhotosPanel flows', () => {
  it('updates document metadata via PATCH', async () => {
    const apiClient = mocks.apiClient
    apiClient.get.mockResolvedValueOnce([]).mockResolvedValueOnce([])
    apiClient.patch.mockResolvedValueOnce({ message: 'ok' })

    const wrapper = mount(DocsPhotosPanel, { global: { stubs: PrimeStubs } })

    wrapper.vm.openDocEditor({ id: 'd1', category: 'c', tags: 't', status: 'reviewed' })
    wrapper.vm.docEditor.category = 'notes'
    wrapper.vm.docEditor.tags = 'tag1'
    wrapper.vm.docEditor.status = 'archived'

    await wrapper.vm.saveDocEditor()

    expect(apiClient.patch).toHaveBeenCalledWith('/api/docs/d1', {
      category: 'notes',
      tags: 'tag1',
      status: 'archived',
    })
  })

  it('deletes photo via DELETE', async () => {
    const apiClient = mocks.apiClient
    apiClient.get.mockResolvedValueOnce([]).mockResolvedValueOnce([])
    apiClient.delete.mockResolvedValueOnce({ message: 'deleted' })

    const wrapper = mount(DocsPhotosPanel, { global: { stubs: PrimeStubs } })
    await wrapper.vm.deletePhoto({ id: 'p1', filename: 'x.png' })
    expect(apiClient.delete).toHaveBeenCalledWith('/api/photos/p1')
  })
})
