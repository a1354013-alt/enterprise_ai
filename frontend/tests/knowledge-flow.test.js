import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

import KnowledgeBase from '../src/components/KnowledgeBase.vue'
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

describe('KnowledgeBase flows', () => {
  it('creates knowledge entry with status/source/related_item_ids', async () => {
    const apiClient = mocks.apiClient
    apiClient.post.mockResolvedValueOnce({ message: 'ok' })
    apiClient.get.mockResolvedValueOnce([])

    const wrapper = mount(KnowledgeBase, { global: { stubs: PrimeStubs } })

    wrapper.vm.entry.problem = 'Problem'
    wrapper.vm.entry.solution = 'Solution'
    wrapper.vm.entry.status = 'draft'
    wrapper.vm.entry.source_type = 'manual'
    wrapper.vm.entry.source_ref = ''
    wrapper.vm.entry.related_item_ids = ['document:doc123', 'photo:ph1']

    await wrapper.vm.saveEntry()

    expect(apiClient.post).toHaveBeenCalledTimes(1)
    expect(apiClient.post.mock.calls[0][0]).toBe('/api/knowledge/entries')
    expect(apiClient.post.mock.calls[0][1]).toMatchObject({
      problem: 'Problem',
      solution: 'Solution',
      status: 'draft',
      source_type: 'manual',
      related_item_ids: ['document:doc123', 'photo:ph1'],
    })
  })

  it('edits knowledge entry via patch including related_item_ids', async () => {
    const apiClient = mocks.apiClient
    apiClient.patch.mockResolvedValueOnce({ message: 'updated' })
    apiClient.get.mockResolvedValueOnce([])

    const wrapper = mount(KnowledgeBase, { global: { stubs: PrimeStubs } })
    wrapper.vm.openEditor({
      id: 'k1',
      title: 'Title',
      problem: 'P',
      root_cause: '',
      solution: 'S',
      tags: '',
      notes: '',
      status: 'reviewed',
      source_type: 'document-derived',
      source_ref: 'document:doc123',
      related_item_ids: ['document:doc123'],
    })

    wrapper.vm.editor.tags = 'tag1'
    wrapper.vm.editor.related_item_ids = ['document:doc123', 'prompt:p1']

    await wrapper.vm.saveEditor()

    expect(apiClient.patch).toHaveBeenCalledWith('/api/knowledge/entries/k1', expect.any(Object))
    const payload = apiClient.patch.mock.calls[0][1]
    expect(payload).toMatchObject({
      tags: 'tag1',
      source_type: 'document-derived',
      source_ref: 'document:doc123',
      related_item_ids: ['document:doc123', 'prompt:p1'],
    })
  })
})
