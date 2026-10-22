import React, { useState } from 'react'

export default function IssueCard({ issue, onApprove }) {
  const [activeTab, setActiveTab] = useState('final')
  const [approving, setApproving] = useState(false)
  const [postedUrl, setPostedUrl] = useState(issue.posted_url || null)
  const [approveError, setApproveError] = useState(null)

  const original = issue.original || {}
  const judge = issue.judge || null
  const final = issue.final || original
  const models = issue.models_used || {}

  // Determine current draft to display according to active tab
  const currentDraft = activeTab === 'original' ? original : final

  // Determine score badge styling
  const score = judge ? judge.score : null
  let scoreClass = 'score-mid'
  if (score !== null) {
    if (score >= 8) scoreClass = 'score-high'
    else if (score < 5) scoreClass = 'score-low'
  }

  const handleApproveClick = async () => {
    setApproving(true)
    setApproveError(null)
    try {
      const url = await onApprove(final)
      setPostedUrl(url)
    } catch (err) {
      setApproveError(err.message || 'Failed to approve issue.')
    } finally {
      setApproving(false)
    }
  }

  return (
    <div className="issue-card">
      {/* Issue Header */}
      <div className="issue-header">
        <div className="issue-title-area">
          <h3 className="issue-title">{currentDraft.title || 'Untitled Issue'}</h3>
          <div className="issue-badges">
            <span className={`badge-tag badge-${currentDraft.difficulty || 'beginner'}`}>
              Level: {currentDraft.difficulty || 'beginner'}
            </span>
            <span className="badge-tag">
              Source: {currentDraft.source || 'repository'}
            </span>
            {activeTab === 'final' && original.title !== final.title && (
              <span className="badge-tag" style={{ borderColor: 'var(--accent-blue)', color: 'var(--accent-blue)' }}>
                ✨ Judge-Polished
              </span>
            )}
          </div>
        </div>

        {score !== null && (
          <div className={`score-badge ${scoreClass}`} title="Judge Quality Score">
            <span>Score:</span>
            <span>{score}/10</span>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="tabs-bar">
        <button
          className={`tab-btn ${activeTab === 'final' ? 'active' : ''}`}
          onClick={() => setActiveTab('final')}
        >
          Final Rewritten
        </button>
        <button
          className={`tab-btn ${activeTab === 'judge' ? 'active' : ''}`}
          onClick={() => setActiveTab('judge')}
        >
          Judge Critique {judge ? `(${judge.score}/10)` : ''}
        </button>
        <button
          className={`tab-btn ${activeTab === 'original' ? 'active' : ''}`}
          onClick={() => setActiveTab('original')}
        >
          Original Draft
        </button>
      </div>

      {/* Tab Body */}
      <div className="tab-content">
        {activeTab === 'judge' ? (
          <div>
            {judge ? (
              <div className="critique-card">
                <div className="content-label">Judge Evaluation & Critique:</div>
                <p className="critique-quote">"{judge.critique}"</p>

                {judge.problems && judge.problems.length > 0 && (
                  <div>
                    <div className="content-label" style={{ color: 'var(--accent-red)' }}>
                      Identified Shortcomings:
                    </div>
                    <ul className="problems-list">
                      {judge.problems.map((prob, idx) => (
                        <li key={idx}>{prob}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)' }}>No judge evaluation was recorded for this draft.</p>
            )}
          </div>
        ) : (
          <div>
            {/* Context */}
            <div className="content-block">
              <div className="content-label">Context & Problem Description:</div>
              <p className="context-text">{currentDraft.context}</p>
            </div>

            {/* Files to touch */}
            <div className="content-block">
              <div className="content-label">Files to Touch:</div>
              {currentDraft.files_to_touch && currentDraft.files_to_touch.length > 0 ? (
                <div className="file-chips">
                  {currentDraft.files_to_touch.map((f, idx) => (
                    <span key={idx} className="file-chip">
                      {f}
                    </span>
                  ))}
                </div>
              ) : (
                <span style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>No existing files touched.</span>
              )}
            </div>

            {/* New Files to create */}
            {currentDraft.new_files && currentDraft.new_files.length > 0 && (
              <div className="content-block">
                <div className="content-label" style={{ color: 'var(--accent-green-bright)' }}>New Files to Create:</div>
                <div className="file-chips">
                  {currentDraft.new_files.map((f, idx) => (
                    <span key={idx} className="file-chip" style={{ borderColor: 'var(--accent-green-bright)', color: 'var(--accent-green-bright)' }}>
                      + {f}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Acceptance Criteria */}
            <div className="content-block">
              <div className="content-label">Acceptance Criteria:</div>
              <ul className="checklist">
                {(currentDraft.acceptance_criteria || []).map((crit, idx) => (
                  <li key={idx} className="checklist-item">
                    <span className="checklist-box" />
                    <span>{crit}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="issue-footer">
        <div className="models-used-tags">
          {models.drafter && (
            <span className="model-tag">
              <strong>Drafter:</strong> {models.drafter.split('/').pop()}
            </span>
          )}
          {models.judge && (
            <span className="model-tag">
              <strong>Judge:</strong> {models.judge.split('/').pop()}
            </span>
          )}
        </div>

        <div>
          {postedUrl ? (
            <a href={postedUrl} target="_blank" rel="noopener noreferrer" className="posted-link">
              <span>✅ Posted to GitHub</span>
              <span>↗</span>
            </a>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.3rem' }}>
              <button
                className="approve-btn"
                onClick={handleApproveClick}
                disabled={approving}
              >
                {approving ? 'Posting to GitHub...' : 'Approve & Post to GitHub'}
              </button>
              {approveError && (
                <span style={{ color: 'var(--accent-red)', fontSize: '0.75rem' }}>
                  {approveError}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
