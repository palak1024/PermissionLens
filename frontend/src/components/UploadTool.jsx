import { useCallback, useRef, useState } from 'react'
import { analyzeApk } from '../lib/api'
import ReportCard from './ReportCard'

const MAX_SIZE_MB = 150

export default function UploadTool() {
  const [status, setStatus] = useState('idle') // idle | scanning | done | error
  const [dragActive, setDragActive] = useState(false)
  const [fileMeta, setFileMeta] = useState(null)
  const [error, setError] = useState('')
  const [report, setReport] = useState(null)
  const inputRef = useRef(null)

  const runAnalysis = useCallback(async (file) => {
    setError('')

    if (!file.name.toLowerCase().endsWith('.apk')) {
      setError('That file doesn\u2019t look like an APK. PermissionLens only reads .apk packages.')
      setStatus('error')
      return
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`This file is larger than the ${MAX_SIZE_MB}MB demo limit.`)
      setStatus('error')
      return
    }

    setFileMeta({ name: file.name, size: (file.size / (1024 * 1024)).toFixed(1) })
    setStatus('scanning')
    try {
      const result = await analyzeApk(file)
      setReport(result)
      setStatus('done')
    } catch (err) {
      setError('Something went wrong while analyzing this file. Try again.')
      setStatus('error')
    }
  }, [])

  const handleFiles = (fileList) => {
    const file = fileList?.[0]
    if (file) runAnalysis(file)
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragActive(false)
    handleFiles(e.dataTransfer.files)
  }

  const reset = () => {
    setStatus('idle')
    setReport(null)
    setFileMeta(null)
    setError('')
  }

  return (
    <section className="tool" id="scan">
      <div className="wrap">
        <div className="tool-head">
          <h2>Inspect an APK</h2>
          <p>Drop a file below, or pick one from your device. Nothing is installed or executed &mdash; only the package contents are read.</p>
        </div>

        {status === 'scanning' && <Scanning fileMeta={fileMeta} />}

        {(status === 'idle' || status === 'error') && (
          <div
            className={`dropzone${dragActive ? ' drag' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragActive(true) }}
            onDragLeave={() => setDragActive(false)}
            onDrop={onDrop}
          >
            <div className="dropzone-icon" aria-hidden="true" />
            <h3>Drag and drop an .apk file</h3>
            <p>or choose one manually from your device</p>
            <button type="button" className="file-input-btn" onClick={() => inputRef.current?.click()}>
              Choose APK file
            </button>
            <input
              ref={inputRef}
              type="file"
              accept=".apk"
              hidden
              onChange={(e) => handleFiles(e.target.files)}
            />
            <div className="dropzone-hint">MAX {MAX_SIZE_MB}MB &middot; ANALYZED LOCALLY IN YOUR SESSION</div>
            {status === 'error' && <div className="error-banner">{error}</div>}
          </div>
        )}

        {status === 'done' && report && <ReportCard report={report} onReset={reset} />}
      </div>
    </section>
  )
}

function Scanning({ fileMeta }) {
  return (
    <div className="scanning">
      <div className="scan-file-row">
        <span>{fileMeta?.name}</span>
        <span>{fileMeta?.size} MB</span>
      </div>
      <div className="scan-panel">
        <div className="scan-line" />
      </div>
      <div className="scan-status">READING MANIFEST &middot; EXTRACTING PERMISSIONS &middot; CROSS-CHECKING CONTEXT&hellip;</div>
    </div>
  )
}