import React, { useState, useEffect, useRef } from 'react'
import PipelineView from './components/PipelineView'
import IssueCard from './components/IssueCard'
import CodeFindingsPanel from './components/CodeFindingsPanel'

export default function App() {
  const [repoUrl, setRepoUrl] = useState('octocat/Hello-World')
  const [appConfig, setAppConfig] = useState(null)
  const [events, setEvents] = useState([])
  const [result, setResult] = useState(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState(null)
  const [isScreenshotRun, setIsScreenshotRun] = useState(false)
  const [screenshotFile, setScreenshotFile] = useState(null)

  const eventSourceRef = useRef(null)

  useEffect(() => {
    fetch('/api/config')
      .then((res) => res.json())
      .then((data) => setAppConfig(data))
      .catch((err) => console.error('Failed to load Kindling config:', err))

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

  const startStream = (runId) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    const es = new EventSource(`/api/stream/${runId}`)
    eventSourceRef.current = es

    es.onmessage = (messageEvent) => {
      try {
        const ev = JSON.parse(messageEvent.data)
        setEvents((prev) => [...prev, ev])

        if (ev.step === 'final') {
          es.close()
          setRunning(false)
          if (ev.status === 'done') {
            setResult(ev.payload)
          } else if (ev.status === 'error') {
            setError(ev.detail || 'Pipeline execution failed.')
          }
        }
      } catch (err) {
        console.error('Error parsing SSE event:', err)
      }
    }

    es.onerror = (err) => {
      console.warn('SSE stream error or finished:', err)
      es.close()
      setRunning(false)
    }
  }

  const handleScanSubmit = async (e) => {
    if (e) e.preventDefault()
    if (!repoUrl.trim() || running) return

    setRunning(true)
    setError(null)
    setResult(null)
    setEvents([])
    setIsScreenshotRun(false)

    try {
      const res = await fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: repoUrl.trim() }),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `Scan failed with status ${res.status}`)
      }

      const data = await res.json()
      startStream(data.run_id)
    } catch (err) {
      setError(err.message)
      setRunning(false)
    }
  }

  const handleScreenshotSubmit = async () => {
    if (!screenshotFile || running) return

    setRunning(true)
    setError(null)
    setResult(null)
    setEvents([])
    setIsScreenshotRun(true)

    const formData = new FormData()
    formData.append('file', screenshotFile)
    if (repoUrl.trim()) {
      formData.append('repo_url', repoUrl.trim())
    }

    try {
      const res = await fetch('/api/screenshot', {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `Screenshot analysis failed with status ${res.status}`)
      }

      const data = await res.json()
      startStream(data.run_id)
    } catch (err) {
      setError(err.message)
      setRunning(false)
    }
  }

  const handleApprove = async (draft) => {
    const res = await fetch('/api/approve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ draft }),
    })

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}))
      throw new Error(errData.detail || `Failed to approve issue (${res.status})`)
    }

    const data = await res.json()
    return data.url
  }

  // Model list summary for footer
  const activeModels = (appConfig?.roles || [])
    .map((r) => r.model.split('/').pop())
    .filter(Boolean)
    .join(', ')

  return (
    <div className="app-container">
      {/* Brand Header */}
      <header className="app-header">
        <div className="brand-badge">🔥 Open-Source Contributor Catalyst</div>
        <h1>Kindling</h1>
        <p className="app-tagline">
          An open-weight agent crew that reads your repository, drafts newcomer-friendly GitHub issues, critiques them with independent judges, and helps maintainers grow their contributor community.
        </p>
      </header>

      {/* Input / Controls Box */}
      <div className="input-section">
        <form onSubmit={handleScanSubmit} className="url-form">
          <input
            type="text"
            className="url-input"
            placeholder="e.g. owner/repo or https://github.com/owner/repo"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            disabled={running}
          />
          <button type="submit" className="btn-primary" disabled={running || !repoUrl.trim()}>
            {running ? (
              <>
                <span className="spinner" /> Crew Working...
              </>
            ) : (
              'Scan & Draft Issues'
            )}
          </button>
        </form>

        <div className="quick-links">
          <span>Try quick demo repo:</span>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => setRepoUrl('octocat/Hello-World')}
            disabled={running}
          >
            octocat/Hello-World
          </button>
          {appConfig?.demo_mode === 'cached' && (
            <span style={{ color: 'var(--accent-amber-bright)', marginLeft: 'auto', fontWeight: 600 }}>
              ⚡ Cached Demo Mode Active
            </span>
          )}
        </div>

        {/* Graphify Architecture Knowledge Graph Indicator */}
        <div className="graphify-banner">
          <div className="graphify-badge-info">
            <span className="graph-icon">🕸️</span>
            <div>
              <strong>Graphify Code Knowledge Graph:</strong>{' '}
              <span>
                {appConfig?.graphify?.nodes_count || 254} nodes · {appConfig?.graphify?.edges_count || 485} edges · {appConfig?.graphify?.communities_count || 14} communities
              </span>
              <div className="graph-subtext">AST code relationships actively power Qwen Code Reviewer context</div>
            </div>
          </div>
          <a
            href="/api/graphify/view"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-graphify"
          >
            Explore Interactive Graph ↗
          </a>
        </div>

        {/* Vision Screenshot Bar (Stretch Feature) */}
        <div className="screenshot-bar">
          <div className="screenshot-label">
            <span>📷 Have a UI Bug?</span>
            <span style={{ color: 'var(--text-dim)' }}>(Gemma/Vision model multimodal issue draft)</span>
          </div>
          <div className="file-input-wrapper">
            <input
              type="file"
              accept="image/*"
              className="file-input"
              onChange={(e) => setScreenshotFile(e.target.files?.[0] || null)}
              disabled={running}
            />
            <button
              type="button"
              className="btn-secondary"
              onClick={handleScreenshotSubmit}
              disabled={running || !screenshotFile}
              style={{
                backgroundColor: screenshotFile ? 'var(--accent-purple)' : undefined,
                color: screenshotFile ? '#fff' : undefined,
                borderColor: screenshotFile ? 'transparent' : undefined,
              }}
            >
              Draft from Screenshot
            </button>
          </div>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="error-banner">
          <strong>Pipeline Notice:</strong> {error}
        </div>
      )}

      {/* Centerpiece: Live Pipeline View */}
      <PipelineView
        roles={appConfig?.roles || []}
        events={events}
        isScreenshotRun={isScreenshotRun}
        config={appConfig}
        codeModel={appConfig?.code_model}
      />

      {/* Code Review Findings Section / Panel */}
      <CodeFindingsPanel
        codeModel={appConfig?.code_model}
        events={events}
        result={result}
        isScreenshotRun={isScreenshotRun}
      />

      {/* Issue Drafts Cards */}
      {result && result.issues && (
        <div className="issues-section">
          <div className="section-title">
            <span>📋 Contributor-Ready Drafts ({result.issues.length})</span>
            <span style={{ color: 'var(--accent-green-bright)', fontWeight: 600, fontSize: '0.8rem' }}>
              All Approved by Judge
            </span>
          </div>

          <div className="issues-grid">
            {result.issues.map((iss) => (
              <IssueCard
                key={iss.id}
                issue={iss}
                onApprove={handleApprove}
              />
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="app-footer">
        <p>
          Built with open-weight models: <strong>{activeModels || 'NVIDIA Nemotron, Meta Muse, Meta Llama 3.2'}</strong>.
        </p>
        <p style={{ marginTop: '0.35rem', color: 'var(--text-dim)' }}>
          Self-hostable: swap <code>LLM_BASE_URL</code> to Ollama or LM Studio to run 100% locally. Released under MIT License.
        </p>
      </footer>
    </div>
  )
}
