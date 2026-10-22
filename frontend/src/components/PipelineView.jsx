import React from 'react'

export default function PipelineView({ roles = [], events = [], isScreenshotRun = false }) {
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
    nodes.push({
      key: 'github',
      step: 'github',
      role: 'GitHub Ingestion',
      model: 'GitHub REST API',
      license: 'REST API',
      why: 'Fetches directory tree, README, open issues, and scans source code for TODO/FIXME markers.',
    })

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

  const judgeRole = roleMap['judge'] || {}
  nodes.push({
    key: 'judge',
    step: 'judge',
    role: 'Independent Judge',
    model: judgeRole.model || 'Judge LLM',
    license: judgeRole.license || 'Open-weight',
    why: judgeRole.why || 'Different model family evaluating clarity, newcomer scoping, and file paths.',
  })

  const drafterRole = roleMap['drafter'] || {}
  nodes.push({
    key: 'rewrite',
    step: 'rewrite',
    role: 'Quality Rewrite',
    model: drafterRole.model || 'Drafter LLM',
    license: drafterRole.license || 'Open-weight',
    why: 'Applies Judge critiques to fix ambiguities, refine acceptance criteria, and enforce accuracy.',
  })

  return (
    <div className="pipeline-section">
      <div className="section-title">
        <span>⚡ Open-Weight Agent Pipeline</span>
        {events.length > 0 && <span style={{ color: 'var(--text-dim)', fontWeight: 400 }}>({events.length} events streamed)</span>}
      </div>

      <div className="pipeline-grid">
        {nodes.map((node) => {
          const ev = eventMap[node.step]
          const status = ev ? ev.status : 'waiting'
          const duration = ev && ev.duration_ms ? `${(ev.duration_ms / 1000).toFixed(1)}s` : null
          const detail = ev && ev.detail ? ev.detail : null

          return (
            <div key={node.key} className={`pipeline-node status-${status}`}>
              <div className="node-header">
                <span className="node-role">{node.role}</span>
                <span className={`node-status-chip chip-${status}`}>{status}</span>
              </div>

              <div className="node-model" title={node.model}>
                {node.model.split('/').pop()}
              </div>

              <div className="node-why">
                {detail ? <strong style={{ color: 'var(--text-main)' }}>{detail}</strong> : node.why}
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
