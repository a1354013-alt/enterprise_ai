export function createObjectUrl(blob: Blob): string {
  if (typeof window === 'undefined' || !window.URL?.createObjectURL) {
    return ''
  }
  return window.URL.createObjectURL(blob)
}

export function revokeObjectUrl(url: string): void {
  try {
    if (typeof window !== 'undefined' && window.URL?.revokeObjectURL) {
      window.URL.revokeObjectURL(url)
    }
  } catch {
    // ignore
  }
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = createObjectUrl(blob)
  if (!url) {
    return
  }
  const link = document.createElement('a')
  link.href = url
  link.download = filename || 'download'
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => revokeObjectUrl(url), 5000)
}

export function openBlobInNewTab(blob: Blob): void {
  const url = createObjectUrl(blob)
  if (!url) {
    return
  }
  window.open(url, '_blank', 'noopener,noreferrer')
  setTimeout(() => revokeObjectUrl(url), 15000)
}
