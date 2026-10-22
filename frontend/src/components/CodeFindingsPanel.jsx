import React, { useState } from 'react'

export default function CodeFindingsPanel({
  codeModel = '',
  events = [],
  result = null,
  isScreenshotRun = false,
}) {
  const [expanded, setExpanded] = useState(true)

  // Don't show code review findings for pure screenshot visual bug runs
  if (isScreenshotRun) {
    return null
  }

  // Find latest code_analysis event
  const codeEvent = events.slice().reverse().find((e) => e.step === 'code_analysis')

  // Check if code review model is configured
  const isConfigured = Boolean(
    codeModel &&
    codeModel.trim() &&
    codeModel !== 'Not configured' &&
    (!codeEvent || codeEvent.model !== 'Not configured')
  )

  // Determine current pipeline status
  let status = 'waiting'
  if (codeEvent) {
    status = codeEvent.status
  } else if (!isConfigured) {
    status = 'skipped'
  } else {
    status = 'waiting'
  }

  // Findings from event payload or final result
  const findingsFromEvent = codeEvent?.payload?.findings
  const findingsFromResult = result?.code_findings
  const findings = findingsFromResult ?? findingsFromEvent ?? null

  const filesAnalyzed = codeEvent?.payload?.files_analyzed
  const findingsCount = Array.isArray(findings) ? findings.length : (codeEvent?.payload?.findings_count ?? 0)

  // Dynamic model label
  const activeModelName = codeEvent?.model || codeModel || ''
  const modelBrand = activeModelName.toLowerCase().includes('nemotron')
    ? 'Nemotron'
    : (activeModelName.toLowerCase().includes('qwen') ? 'Qwen' : 'Code Reviewer')

  // State 1: Skipped because code model is not configured
  if (status === 'skipped' || !isConfigured) {
    return (
      <div className="findings-panel findings-panel-skipped">
        <div className="findings-header">
          <div className="findings-title-area">
            <span className="findings-title">🔍 Code Reviewer ({modelBrand}) Findings</span>
            <span className="node-status-chip chip-skipped">SKIPPED</span>
          </div>
        </div>
        <div className="findings-body">
          <p className="findings-notice">
            Code analysis skipped because code model is not configured.
          </p>
          <p className="findings-subnotice">
            To enable deep source code analysis, set <code>CODE_MODEL</code> in your backend <code>.env</code> file (e.g. <code>CODE_MODEL=nvidia/nemotron-3-ultra-550b-a55b</code>).
          </p>
        </div>
      </div>
    )
  }

  // State 2: Failed with an error
  if (status === 'error') {
    return (
      <div className="findings-panel findings-panel-error">
        <div className="findings-header">
          <div className="findings-title-area">
            <span className="findings-title">🔍 Code Reviewer ({modelBrand}) Findings</span>
            <span className="node-status-chip chip-error">ERROR</span>
          </div>
        </div>
        <div className="findings-body">
          <p className="findings-notice error-text">
            Code analysis failed.
          </p>
          <p className="findings-subnotice">
            {codeEvent?.detail || 'An unexpected error occurred during code analysis.'}
          </p>
          {codeEvent?.detail?.includes('404') && (
            <p className="findings-subnotice" style={{ marginTop: '0.5rem', color: 'var(--accent-amber-bright)' }}>
              💡 <strong>Tip:</strong> The configured <code>CODE_MODEL</code> was not found on your current LLM provider endpoint. Leave <code>CODE_MODEL=</code> empty in <code>.env</code> to skip this stage cleanly, or point <code>LLM_BASE_URL</code> to a local Ollama/LM Studio server hosting Qwen.
            </p>
          )}
        </div>
      </div>
    )
  }

  // State 3: Analysis in progress
  if (status === 'running') {
    return (
      <div className="findings-panel findings-panel-running">
        <div className="findings-header">
          <div className="findings-title-area">
            <span className="findings-title">🔍 Code Reviewer ({modelBrand}) Findings</span>
            <span className="node-status-chip chip-running">RUNNING</span>
          </div>
        </div>
        <div className="findings-body">
          <p className="findings-notice">
            <span className="spinner" /> Code analysis in progress...
          </p>
          <p className="findings-subnotice">
            {modelBrand} is analyzing repository source files for concrete bugs, edge cases, and code smells.
          </p>
        </div>
      </div>
    )
  }

  // State 4: Has not started yet
  if ((status === 'waiting' || status === 'not_started') && !result && (!findings || findings.length === 0)) {
    return (
      <div className="findings-panel findings-panel-waiting">
        <div className="findings-header">
          <div className="findings-title-area">
            <span className="findings-title">🔍 Code Reviewer ({modelBrand}) Findings</span>
            <span className="node-status-chip chip-waiting">WAITING</span>
          </div>
        </div>
        <div className="findings-body">
          <p className="findings-notice">
            Code analysis has not started.
          </p>
          <p className="findings-subnotice">
            Configured model: <code>{codeModel}</code>. Start a scan to begin reviewing repository source files.
          </p>
        </div>
      </div>
    )
  }

  // State 5: Completed with zero findings
  if (Array.isArray(findings) && findings.length === 0) {
    return (
      <div className="findings-panel findings-panel-done">
        <div className="findings-header">
          <div className="findings-title-area">
            <span className="findings-title">🔍 Code Reviewer ({modelBrand}) Findings (0)</span>
            <span className="node-status-chip chip-done">COMPLETED</span>
          </div>
        </div>
        <div className="findings-body">
          <p className="findings-notice success-text">
            No code findings returned.
          </p>
          <p className="findings-subnotice">
            {filesAnalyzed !== undefined ? `${filesAnalyzed} source files were inspected. ` : ''}
            The analyzed source files contained no detected bugs, or the code was clean.
          </p>
        </div>
      </div>
    )
  }

  // State 6: Completed with findings list
  if (Array.isArray(findings) && findings.length > 0) {
    return (
      <div className="findings-panel findings-panel-done">
        <div className="findings-header">
          <div className="findings-title-area">
            <span className="findings-title">
              🔍 Code Reviewer ({modelBrand}) Findings ({findings.length})
            </span>
            <span className="node-status-chip chip-done">COMPLETED</span>
          </div>
          <div className="findings-meta-right">
            {filesAnalyzed !== undefined && (
              <span className="findings-meta-item">
                📁 {filesAnalyzed} files inspected
              </span>
            )}
            <button
              type="button"
              className="btn-toggle-expand"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? '▲ Collapse' : '▼ Expand'}
            </button>
          </div>
        </div>

        {expanded && (
          <div className="findings-list">
            {findings.map((f, idx) => {
              const severity = (f.severity || 'medium').toLowerCase()
              const titleText = f.title || f.explanation || `Finding #${idx + 1}`
              const showSeparateDesc = f.title && f.explanation && f.title !== f.explanation

              return (
                <div key={idx} className="finding-card">
                  <div className="finding-card-header">
                    <span className="finding-title">{titleText}</span>
                    <span className={`severity-badge severity-${severity}`}>
                      {severity.toUpperCase()}
                    </span>
                  </div>

                  <div className="finding-location">
                    <span className="finding-path" title={f.file_path}>
                      📄 {f.file_path}
                    </span>
                    {f.line_range && (
                      <span className="finding-lines">
                        Lines: {f.line_range}
                      </span>
                    )}
                  </div>

                  {showSeparateDesc && (
                    <div className="finding-desc">
                      {f.explanation}
                    </div>
                  )}

                  {f.evidence && (
                    <div className="finding-evidence-section">
                      <div className="evidence-header">Code Evidence:</div>
                      <pre className="evidence-snippet">
                        <code>{f.evidence}</code>
                      </pre>
                    </div>
                  )}

                  {f.suggested_fix && (
                    <div className="finding-fix-section">
                      <span className="fix-label">Suggested Fix:</span> {f.suggested_fix}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    )
  }

  // Fallback completed state if findings array not yet hydrated
  return (
    <div className="findings-panel findings-panel-done">
      <div className="findings-header">
        <div className="findings-title-area">
          <span className="findings-title">🔍 Code Reviewer ({modelBrand}) Findings</span>
          <span className="node-status-chip chip-done">COMPLETED</span>
        </div>
      </div>
      <div className="findings-body">
        <p className="findings-notice">
          {codeEvent?.detail || `${findingsCount} findings reported.`}
        </p>
      </div>
    </div>
  )
}
