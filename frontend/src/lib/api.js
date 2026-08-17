import { analyzeLocally } from './mockAnalysis'

const API_URL = import.meta.env.VITE_API_URL // set on Vercel once the FastAPI backend is deployed

// Simulates the few seconds a real static-analysis pass takes, so the
// scanning animation has something honest to show even in demo mode.
function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function analyzeApk(file) {
  if (API_URL) {
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await fetch(`${API_URL}/analyze`, { method: 'POST', body: form })
      if (!res.ok) throw new Error(`Backend responded ${res.status}`)
      const data = await res.json()
      return { ...data, source: 'backend' }
    } catch (err) {
      console.warn('Backend analysis failed, falling back to local demo mode:', err)
    }
  }
  await wait(2200)
  return analyzeLocally(file)
}