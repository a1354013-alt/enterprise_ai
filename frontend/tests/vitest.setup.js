import { vi } from 'vitest'

if (typeof window !== 'undefined') {
  window.confirm = () => true
}

if (!globalThis.navigator) {
  globalThis.navigator = {}
}

if (!globalThis.navigator.clipboard) {
  globalThis.navigator.clipboard = {
    writeText: vi.fn(async () => {}),
  }
}

