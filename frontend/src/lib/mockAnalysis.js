// Local, deterministic stand-in for the FastAPI risk engine (Phases 2–4 of
// the project). This lets the frontend be demoed and deployed on its own,
// and gets swapped for the real /analyze response once VITE_API_URL points
// at the live backend — see lib/api.js.

const PERMISSION_INFO = {
  INTERNET: { label: 'Internet access', sensitivity: 'low' },
  ACCESS_NETWORK_STATE: { label: 'View network status', sensitivity: 'low' },
  CAMERA: { label: 'Camera', sensitivity: 'high' },
  RECORD_AUDIO: { label: 'Microphone', sensitivity: 'high' },
  ACCESS_FINE_LOCATION: { label: 'Precise location', sensitivity: 'high' },
  ACCESS_COARSE_LOCATION: { label: 'Approximate location', sensitivity: 'medium' },
  READ_CONTACTS: { label: 'Contacts', sensitivity: 'high' },
  READ_SMS: { label: 'SMS messages', sensitivity: 'high' },
  SEND_SMS: { label: 'Send SMS', sensitivity: 'high' },
  READ_EXTERNAL_STORAGE: { label: 'Files & media (read)', sensitivity: 'medium' },
  WRITE_EXTERNAL_STORAGE: { label: 'Files & media (write)', sensitivity: 'medium' },
  READ_PHONE_STATE: { label: 'Phone identity / status', sensitivity: 'medium' },
  BLUETOOTH: { label: 'Bluetooth', sensitivity: 'low' },
  POST_NOTIFICATIONS: { label: 'Send notifications', sensitivity: 'low' },
  READ_CALL_LOG: { label: 'Call log', sensitivity: 'high' },
}

// What a given app category can reasonably justify.
const CATEGORY_PROFILES = {
  calculator: {
    label: 'Calculator',
    expected: ['INTERNET', 'ACCESS_NETWORK_STATE'],
  },
  flashlight: {
    label: 'Flashlight / Utility',
    expected: ['CAMERA', 'INTERNET'],
  },
  camera: {
    label: 'Camera app',
    expected: ['CAMERA', 'READ_EXTERNAL_STORAGE', 'WRITE_EXTERNAL_STORAGE', 'ACCESS_FINE_LOCATION'],
  },
  messaging: {
    label: 'Messaging app',
    expected: ['READ_SMS', 'SEND_SMS', 'READ_CONTACTS', 'INTERNET', 'POST_NOTIFICATIONS'],
  },
  generic: {
    label: 'General app',
    expected: ['INTERNET', 'ACCESS_NETWORK_STATE', 'POST_NOTIFICATIONS'],
  },
}

function guessCategory(fileName) {
  const n = fileName.toLowerCase()
  if (n.includes('calc')) return 'calculator'
  if (n.includes('torch') || n.includes('flash') || n.includes('light')) return 'flashlight'
  if (n.includes('cam')) return 'camera'
  if (n.includes('chat') || n.includes('msg') || n.includes('sms')) return 'messaging'
  return 'generic'
}

// Deterministic pseudo-random pick of a permission set, seeded by file name
// + size so the same file always produces the same demo report.
function seededPermissionSet(fileName, fileSize) {
  const seed = Array.from(fileName).reduce((a, c) => a + c.charCodeAt(0), 0) + fileSize
  const all = Object.keys(PERMISSION_INFO)
  const count = 4 + (seed % 5) // 4–8 permissions
  const picked = new Set(['INTERNET'])
  let i = seed
  while (picked.size < count) {
    picked.add(all[i % all.length])
    i += 7
  }
  return Array.from(picked)
}

export function analyzeLocally(file) {
  const category = guessCategory(file.name)
  const profile = CATEGORY_PROFILES[category]
  const permissions = seededPermissionSet(file.name, file.size || 12345)

  const rows = permissions.map((code) => {
    const info = PERMISSION_INFO[code] || { label: code, sensitivity: 'medium' }
    const isExpected = profile.expected.includes(code)
    let status = 'ok'
    if (!isExpected) {
      status = info.sensitivity === 'high' ? 'danger' : 'warn'
    }
    return { code, ...info, status }
  })

  const highConcern = rows.filter((r) => r.status === 'danger')
  const unusual = rows.filter((r) => r.status === 'warn')

  let score = 8
  score += unusual.length * 12
  score += highConcern.length * 22
  score = Math.min(96, score)

  let level = 'low'
  if (score > 30) level = 'medium'
  if (score > 60) level = 'high'
  if (score > 80) level = 'critical'

  const evidence = highConcern
    .filter((r) => ['CAMERA', 'ACCESS_FINE_LOCATION', 'RECORD_AUDIO', 'READ_CONTACTS'].includes(r.code))
    .map((r) => `${r.label}-related API references detected in the package`)

  const concerning = [...highConcern, ...unusual]
  const explanation = concerning.length
    ? `This app is categorized as a ${profile.label.toLowerCase()}. ${concerning
        .slice(0, 3)
        .map((r) => r.label.toLowerCase())
        .join(', ')} ${concerning.length > 1 ? "don't" : "doesn't"} obviously match that purpose${
        evidence.length ? ', and the package contains code paths that reference the underlying hardware' : ''
      }. That doesn't prove misuse — but it's worth checking why it's there.`
    : `Every permission this app requests lines up with what a ${profile.label.toLowerCase()} needs to function. Nothing here stands out as unusual.`

  const recommendations = concerning.length
    ? [
        `Open the app's stated purpose against ${concerning.map((r) => r.label).join(', ')} and confirm each one maps to a real feature.`,
        'Check the developer listing and reviews for mentions of these permissions.',
        'If a feature using this permission is optional, revoke it from system settings and see if the app still works.',
      ]
    : ['No action needed — re-check after major app updates, since new permissions can be added silently.']

  return {
    appName: file.name.replace(/\.apk$/i, '').replace(/[_-]/g, ' '),
    packageName: `com.example.${category}`,
    category: profile.label,
    score,
    level,
    permissions: rows,
    evidence,
    explanation,
    recommendations,
    source: 'local-demo',
  }
}