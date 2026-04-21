import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

import AutoTestPanel from '../src/components/AutoTestPanel.vue'
import { PrimeStubs } from './stubs'

vi.mock('primevue/usetoast', () => ({
  useToast: () => ({ add: vi.fn() }),
}))

const mocks = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
}))

vi.mock('../src/api', () => ({
  get: mocks.get,
  post: mocks.post,
}))

describe('AutoTestPanel flows', () => {
  it('runs autotest upload and loads run details', async () => {
    mocks.post.mockResolvedValueOnce({ id: 'r1', status: 'passed', steps: [] })
    mocks.get.mockResolvedValueOnce([]) // initial loadRuns on mount
    mocks.get.mockResolvedValueOnce([]) // loadRuns after run

    const wrapper = mount(AutoTestPanel, { global: { stubs: PrimeStubs } })
    const vm = wrapper.vm as any
    vm.selectedZip = new File(['zip'], 'proj.zip', { type: 'application/zip' })

    await vm.runAutoTest()

    expect(mocks.post.mock.calls[0][0]).toBe('/api/autotest/run')
  })
})
