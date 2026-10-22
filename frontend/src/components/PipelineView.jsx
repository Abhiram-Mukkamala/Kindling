import React from 'react'

export default function PipelineView({
  roles = [],
  events = [],
  isScreenshotRun = false,
  config = null,
  codeModel = null,
}) {
  // Map of step to the latest event received for that step
  const eventMap = {}
  events.forEach((ev) => {
    eventMap[ev.step] = ev
  })

  // Role lookup from server config
  const roleMap = {}
  roles.forEach((r) => {
    roleMap[r.role] = r
  })

  // Build pipeline nodes list
  const nodes = []

  if (isScreenshotRun) {
    const visionRole = roleMap['vision'] || {}
    nodes.push({
      key: 'vision',
      step: 'vision',
      role: 'Vision Perception',
      model: visionRole.model || 'Multimodal Vision Model',
      license: visionRole.license || 'Open-weight',
      why: visionRole.why || 'Multimodal vision model that converts bug screenshots into structured issue drafts.',
    })
  } else {
    // Stage 1: GitHub Ingestion
    nodes.push({
      key: 'github',
      step: 'github',
      role: 'GitHub Ingestion',
      model: 'GitHub REST API',
      license: 'REST API',
      why: 'Fetches directory tree, README, open issues, and scans source code for TODO/FIXME markers.',
    })

    // Stage 2: Candidate Scanner (Optional)
    if (roleMap['scanner'] && roleMap['scanner'].model) {
      nodes.push({
        key: 'scanner',
        step: 'scanner',
        role: 'Candidate Scanner',
        model: roleMap['scanner'].model,
        license: roleMap['scanner'].license || 'Open-weight',
        why: roleMap['scanner'].why || 'Quickly identifies high-signal opportunities across the repo.',
      })
    }

    // Stage 3: Code Reviewer (Permanently visible)
    // Derive configured code model from direct prop, config object, or roles list
    const rawCodeModel = (
      codeModel ??
      config?.code_model ??
      roleMap['code_analysis']?.model ??
      ''
    )
    const configuredCodeModel = (typeof rawCodeModel === 'string' ? rawCodeModel : '').trim()
    const codeEvent = eventMap['code_analysis']

    // Model name to display: prefer event model (if not 'Not configured'), then configured model, else 'Not configured'
    let resolvedCodeModel = 'Not configured'
    if (codeEvent && codeEvent.model && codeEvent.model !== 'Not configured') {
      resolvedCodeModel = codeEvent.model
    } else if (configuredCodeModel) {
      resolvedCodeModel = configuredCodeModel
    }

    const isCodeConfigured = resolvedCodeModel !== 'Not configured'

    // Status: waiting, running, done/completed, skipped, error
    let codeStatus = 'waiting'
    if (codeEvent) {
      codeStatus = codeEvent.status
      if (codeStatus === 'waiting' && !isCodeConfigured) {
        codeStatus = 'skipped'
      }
    } else if (!isCodeConfigured) {
      codeStatus = 'skipped'
    } else {
      codeStatus = 'waiting'
    }

    // Detail / description text
    let codeDetail = null
    if (codeStatus === 'error') {
      codeDetail = codeEvent?.detail ? `⚠️ ${codeEvent.detail}` : '⚠️ Code analysis failed'
    } else if (codeStatus === 'skipped') {
      codeDetail = 'CODE_MODEL is not set in backend .env'
    } else if (codeStatus === 'running') {
      codeDetail = 'Analyzing repository source files for bugs and anti-patterns...'
    } else if (codeStatus === 'done' || codeStatus === 'completed') {
      const filesAnalyzed = codeEvent?.payload?.files_analyzed
      const findingsCount = codeEvent?.payload?.findings_count
      if (filesAnalyzed !== undefined || findingsCount !== undefined) {
        codeDetail = `${filesAnalyzed ?? 0} files analyzed · ${findingsCount ?? 0} findings`
      } else if (codeEvent?.detail) {
        codeDetail = codeEvent.detail
      } else {
        codeDetail = 'Analysis completed'
      }
    } else {
      codeDetail = roleMap['code_analysis']?.why || 'Deep source code analysis and evidence extraction to identify concrete bugs.'
    }

    const modelLower = resolvedCodeModel.toLowerCase()
    let codeRole = 'Code Reviewer — Qwen'
    if (modelLower.includes('nemotron')) {
      codeRole = 'Code Reviewer — Nemotron'
    } else if (modelLower.includes('qwen')) {
      codeRole = 'Code Reviewer — Qwen'
    } else if (isCodeConfigured) {
      codeRole = `Code Reviewer — ${resolvedCodeModel.split('/').pop().split('-')[0]}`
    }

    nodes.push({
      key: 'code_analysis',
      step: 'code_analysis',
      role: codeRole,
      model: resolvedCodeModel,
      license: roleMap['code_analysis']?.license || 'Open-weight',
      why: roleMap['code_analysis']?.why || 'Deep source code analysis and evidence extraction to identify concrete bugs.',
      overrideStatus: codeStatus,
      overrideDetail: codeDetail,
    })

    // Stage 4: Issue Drafter
    const drafterRole = roleMap['drafter'] || {}
    nodes.push({
      key: 'drafter',
      step: 'drafter',
      role: 'Issue Drafter',
      model: drafterRole.model || 'Drafter LLM',
      license: drafterRole.license || 'Open-weight',
      why: drafterRole.why || 'Reasoning model that drafts actionable, newcomer-friendly issues from repository context.',
    })
  }

  // Stage 5: Independent Judge
  const judgeRole = roleMap['judge'] || {}
  nodes.push({
    key: 'judge',
    step: 'judge',
    role: 'Independent Judge',
    model: judgeRole.model || 'Judge LLM',
    license: judgeRole.license || 'Open-weight',
    why: judgeRole.why || 'Different model family evaluating clarity, newcomer scoping, and file paths.',
  })

  // Stage 6: Quality Rewrite
  const rewriteRole = roleMap['rewrite'] || {}
  nodes.push({
    key: 'rewrite',
    step: 'rewrite',
    role: 'Quality Rewrite',
    model: rewriteRole.model || roleMap['drafter']?.model || 'Rewrite LLM',
    license: rewriteRole.license || 'Open-weight',
    why: rewriteRole.why || 'Applies Judge critiques to fix ambiguities, refine acceptance criteria, and enforce accuracy.',
  })

  // Map status code to standard uppercase label
  const STATUS_LABELS = {
    waiting: 'WAITING',
    running: 'RUNNING',
    done: 'COMPLETED',
    completed: 'COMPLETED',
    skipped: 'SKIPPED',
    error: 'ERROR',
  }

  return (
    <div className="pipeline-section">
      <div className="section-title">
        <span>⚡ Open-Weight Agent Pipeline</span>
        {events.length > 0 && (
          <span style={{ color: 'var(--text-dim)', fontWeight: 400 }}>
            ({events.length} events streamed)
          </span>
        )}
      </div>

      <div className="pipeline-grid">
        {nodes.map((node) => {
          const ev = eventMap[node.step]
          const rawStatus = node.overrideStatus || (ev ? ev.status : 'waiting')
          const statusKey = rawStatus === 'done' ? 'done' : rawStatus
          const statusLabel = STATUS_LABELS[rawStatus] || rawStatus.toUpperCase()
          const duration = ev && ev.duration_ms ? `${(ev.duration_ms / 1000).toFixed(1)}s` : null
          const detail = node.overrideDetail || (ev && ev.detail ? ev.detail : null)

          return (
            <div key={node.key} className={`pipeline-node status-${statusKey}`}>
              <div className="node-header">
                <span className="node-role">{node.role}</span>
                <span className={`node-status-chip chip-${statusKey}`}>
                  {statusLabel}
                </span>
              </div>

              <div className="node-model" title={node.model}>
                {node.model}
              </div>

              <div className="node-why">
                {rawStatus === 'error' && detail ? (
                  <span style={{ color: 'var(--accent-red)', fontWeight: 600 }}>{detail}</span>
                ) : detail ? (
                  <strong style={{ color: 'var(--text-main)' }}>{detail}</strong>
                ) : (
                  node.why
                )}
              </div>

              <div className="node-footer">
                <span className="node-license">{node.license}</span>
                {duration && <span className="node-duration">⏱ {duration}</span>}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
