const DEFAULT_API_BASE_URL = 'http://localhost:8000'

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL
).replace(/\/$/, '')

function getDetailMessage(detail) {
  if (typeof detail === 'string') {
    return detail
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => (typeof item === 'string' ? item : item?.msg))
      .filter(Boolean)
      .join('. ')
  }

  if (detail && typeof detail === 'object') {
    return detail.msg || detail.message || ''
  }

  return ''
}

export async function uploadProject(file) {
  const formData = new FormData()
  formData.append('file', file)

  let response
  try {
    response = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: 'POST',
      body: formData,
    })
  } catch {
    throw new Error(
      'We could not reach RepoLens. Check that the backend is running and try again.',
    )
  }

  let payload = null
  try {
    payload = await response.json()
  } catch {
    // The response may be empty or not JSON; use a safe status-based message below.
  }

  if (!response.ok) {
    const detail = getDetailMessage(payload?.detail)
    if (response.status >= 500) {
      throw new Error('RepoLens could not analyze this project. Please try again.')
    }

    throw new Error(detail || 'We could not analyze this file. Check the ZIP and try again.')
  }

  if (!payload || typeof payload !== 'object') {
    throw new Error('RepoLens returned an unexpected response. Please try again.')
  }

  return payload
}
