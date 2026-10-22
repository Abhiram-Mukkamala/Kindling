import assert from 'node:assert'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { createServer } from 'vite'

async function runTests() {
  console.log('--- Starting Frontend Code Reviewer Visibility & Verification Tests ---')

  const vite = await createServer({
    server: { middlewareMode: true },
    appType: 'custom',
  })

  try {
    const { default: PipelineView } = await vite.ssrLoadModule('./src/components/PipelineView.jsx')
    const { default: CodeFindingsPanel } = await vite.ssrLoadModule('./src/components/CodeFindingsPanel.jsx')
    const { default: IssueCard } = await vite.ssrLoadModule('./src/components/IssueCard.jsx')

    const baseRoles = [
      { role: 'scanner', model: 'fast-scanner', why: 'Quick scan', license: 'Open-weight' },
      { role: 'code_analysis', model: 'qwen/qwen-2.5-coder-32b-instruct', why: 'Deep code analysis', license: 'Open-weight' },
      { role: 'drafter', model: 'nvidia/nemotron-4-340b-instruct', why: 'Issue drafter', license: 'Open-weight' },
      { role: 'judge', model: 'nvidia/nemotron-nano-4b-instruct', why: 'Strict judge', license: 'Open-weight' },
      { role: 'rewrite', model: 'google/gemma-2-9b-it', why: 'Quality rewrite', license: 'Open-weight' },
    ]

    // Scenario 1: CODE_MODEL configured and code analysis runs successfully with findings
    console.log('Testing Scenario 1: CODE_MODEL configured and runs with findings...')
    {
      const events = [
        { step: 'code_analysis', role: 'code_analysis', model: 'qwen/qwen-2.5-coder-32b-instruct', status: 'done', duration_ms: 1250, payload: { files_analyzed: 4, findings_count: 2, findings: [
          {
            file_path: 'backend/pipeline.py',
            line_range: '42-50',
            severity: 'high',
            title: 'Unchecked null pointer on error payload',
            explanation: 'Accessing payload.detail without checking error response state can cause KeyError.',
            evidence: 'detail = ev["payload"]["detail"]',
            suggested_fix: 'Use ev.get("payload", {}).get("detail")',
          },
          {
            file_path: 'frontend/src/App.jsx',
            line_range: '100',
            severity: 'medium',
            title: 'Unclosed SSE listener',
            explanation: 'EventSource ref should be closed when component unmounts.',
            evidence: 'const es = new EventSource(...)',
            suggested_fix: 'Return cleanup function in useEffect',
          }
        ] } }
      ]

      const pipelineHtml = renderToStaticMarkup(
        React.createElement(PipelineView, {
          roles: baseRoles,
          events,
          codeModel: 'qwen/qwen-2.5-coder-32b-instruct',
        })
      )

      assert(pipelineHtml.includes('Code Reviewer — Qwen'), 'PipelineView must contain node label "Code Reviewer — Qwen"')
      assert(pipelineHtml.includes('qwen/qwen-2.5-coder-32b-instruct'), 'PipelineView must display configured model name')
      assert(pipelineHtml.includes('COMPLETED'), 'PipelineView must show COMPLETED status chip')
      assert(pipelineHtml.includes('4 files analyzed · 2 findings'), 'PipelineView must display files analyzed and findings count')
      assert(pipelineHtml.includes('1.3s'), 'PipelineView must display formatted duration')

      const findingsHtml = renderToStaticMarkup(
        React.createElement(CodeFindingsPanel, {
          codeModel: 'qwen/qwen-2.5-coder-32b-instruct',
          events,
        })
      )

      assert(findingsHtml.includes('Code Reviewer (Qwen) Findings (2)'), 'Panel must show findings count in header')
      assert(findingsHtml.includes('backend/pipeline.py'), 'Panel must show file path')
      assert(findingsHtml.includes('Lines: 42-50'), 'Panel must show line range')
      assert(findingsHtml.includes('HIGH'), 'Panel must show severity badge')
      assert(findingsHtml.includes('Unchecked null pointer on error payload'), 'Panel must show title/explanation')
      assert(findingsHtml.includes('detail = ev[&quot;payload&quot;][&quot;detail&quot;]') || findingsHtml.includes('detail = ev'), 'Panel must show code evidence')
      assert(findingsHtml.includes('Use ev.get(&quot;payload&quot;, {}).get(&quot;detail&quot;)') || findingsHtml.includes('Use ev.get'), 'Panel must show suggested fix')
      console.log('✓ Scenario 1 passed')
    }

    // Scenario 2: CODE_MODEL configured and runs with zero findings
    console.log('Testing Scenario 2: CODE_MODEL configured and runs with zero findings...')
    {
      const events = [
        {
          step: 'code_analysis',
          role: 'code_analysis',
          model: 'qwen/qwen-2.5-coder-32b-instruct',
          status: 'done',
          duration_ms: 900,
          payload: { files_analyzed: 5, findings_count: 0, findings: [] },
        }
      ]

      const pipelineHtml = renderToStaticMarkup(
        React.createElement(PipelineView, {
          roles: baseRoles,
          events,
          codeModel: 'qwen/qwen-2.5-coder-32b-instruct',
        })
      )
      assert(pipelineHtml.includes('5 files analyzed · 0 findings'), 'PipelineView must show 0 findings')

      const findingsHtml = renderToStaticMarkup(
        React.createElement(CodeFindingsPanel, {
          codeModel: 'qwen/qwen-2.5-coder-32b-instruct',
          events,
        })
      )
      assert(findingsHtml.includes('No code findings returned.'), 'Panel must show explicit "No code findings returned." message')
      assert(findingsHtml.includes('COMPLETED'), 'Panel must show COMPLETED chip')
      console.log('✓ Scenario 2 passed')
    }

    // Scenario 3: CODE_MODEL configured but code analysis fails with error
    console.log('Testing Scenario 3: CODE_MODEL configured but fails with error...')
    {
      const events = [
        {
          step: 'code_analysis',
          role: 'code_analysis',
          model: 'qwen/qwen-2.5-coder-32b-instruct',
          status: 'error',
          detail: 'API Rate limit exceeded on Qwen model endpoint',
        }
      ]

      const pipelineHtml = renderToStaticMarkup(
        React.createElement(PipelineView, {
          roles: baseRoles,
          events,
          codeModel: 'qwen/qwen-2.5-coder-32b-instruct',
        })
      )
      assert(pipelineHtml.includes('ERROR'), 'PipelineView must show ERROR status chip')
      assert(pipelineHtml.includes('API Rate limit exceeded on Qwen model endpoint'), 'PipelineView must show error detail')

      const findingsHtml = renderToStaticMarkup(
        React.createElement(CodeFindingsPanel, {
          codeModel: 'qwen/qwen-2.5-coder-32b-instruct',
          events,
        })
      )
      assert(findingsHtml.includes('Code analysis failed.'), 'Panel must show "Code analysis failed."')
      assert(findingsHtml.includes('API Rate limit exceeded on Qwen model endpoint'), 'Panel must show error detail')
      console.log('✓ Scenario 3 passed')
    }

    // Scenario 4: CODE_MODEL empty or unset (skipped state)
    console.log('Testing Scenario 4: CODE_MODEL empty or unset (skipped state)...')
    {
      const rolesWithoutCode = baseRoles.filter(r => r.role !== 'code_analysis')
      const pipelineHtml = renderToStaticMarkup(
        React.createElement(PipelineView, {
          roles: rolesWithoutCode,
          events: [],
          codeModel: '',
          config: { code_model: '' },
        })
      )

      assert(pipelineHtml.includes('Code Reviewer — Qwen'), 'Node must remain visible even when CODE_MODEL is empty')
      assert(pipelineHtml.includes('Not configured'), 'Model must display "Not configured"')
      assert(pipelineHtml.includes('SKIPPED'), 'Status must display SKIPPED')
      assert(pipelineHtml.includes('CODE_MODEL is not set in backend .env'), 'Must explain CODE_MODEL is not set in backend .env')

      const findingsHtml = renderToStaticMarkup(
        React.createElement(CodeFindingsPanel, {
          codeModel: '',
          events: [],
        })
      )
      assert(findingsHtml.includes('Code analysis skipped because Qwen is not configured.'), 'Panel must state code analysis skipped because Qwen is not configured')
      assert(findingsHtml.includes('SKIPPED'), 'Panel chip must be SKIPPED')
      console.log('✓ Scenario 4 passed')
    }

    // Scenario 5: GitHub Ingestion completes, Drafter begins, and Code Reviewer node remains distinct
    console.log('Testing Scenario 5: Node order & distinctiveness during pipeline progression...')
    {
      const events = [
        { step: 'github', role: 'github', model: 'GitHub REST API', status: 'done', duration_ms: 450, detail: '12 files, 3 open issues, 4 TODOs' },
        { step: 'code_analysis', role: 'code_analysis', model: 'qwen/qwen-2.5-coder-32b-instruct', status: 'done', duration_ms: 1100, payload: { files_analyzed: 3, findings_count: 1, findings: [] } },
        { step: 'drafter', role: 'drafter', model: 'nvidia/nemotron-4-340b-instruct', status: 'running' },
      ]

      const pipelineHtml = renderToStaticMarkup(
        React.createElement(PipelineView, {
          roles: baseRoles,
          events,
          codeModel: 'qwen/qwen-2.5-coder-32b-instruct',
        })
      )

      const ghIndex = pipelineHtml.indexOf('GitHub Ingestion')
      const codeIndex = pipelineHtml.indexOf('Code Reviewer — Qwen')
      const drafterIndex = pipelineHtml.indexOf('Issue Drafter')

      assert(ghIndex !== -1, 'GitHub Ingestion must be present')
      assert(codeIndex !== -1, 'Code Reviewer — Qwen must be present')
      assert(drafterIndex !== -1, 'Issue Drafter must be present')
      assert(ghIndex < codeIndex, 'GitHub Ingestion must precede Code Reviewer')
      assert(codeIndex < drafterIndex, 'Code Reviewer must precede Issue Drafter')
      console.log('✓ Scenario 5 passed')
    }

    // Scenario 6: Real-time updates during live event streaming
    console.log('Testing Scenario 6: Real-time event transitions...')
    {
      // Stage A: waiting
      const waitingHtml = renderToStaticMarkup(
        React.createElement(PipelineView, {
          roles: baseRoles,
          events: [{ step: 'code_analysis', role: 'code_analysis', model: 'qwen/qwen-2.5-coder-32b-instruct', status: 'waiting' }],
          codeModel: 'qwen/qwen-2.5-coder-32b-instruct',
        })
      )
      assert(waitingHtml.includes('WAITING'), 'Must show WAITING')

      // Stage B: running
      const runningHtml = renderToStaticMarkup(
        React.createElement(PipelineView, {
          roles: baseRoles,
          events: [
            { step: 'code_analysis', role: 'code_analysis', model: 'qwen/qwen-2.5-coder-32b-instruct', status: 'waiting' },
            { step: 'code_analysis', role: 'code_analysis', model: 'qwen/qwen-2.5-coder-32b-instruct', status: 'running' },
          ],
          codeModel: 'qwen/qwen-2.5-coder-32b-instruct',
        })
      )
      assert(runningHtml.includes('RUNNING'), 'Must show RUNNING')

      // Stage C: done
      const doneHtml = renderToStaticMarkup(
        React.createElement(PipelineView, {
          roles: baseRoles,
          events: [
            { step: 'code_analysis', role: 'code_analysis', model: 'qwen/qwen-2.5-coder-32b-instruct', status: 'waiting' },
            { step: 'code_analysis', role: 'code_analysis', model: 'qwen/qwen-2.5-coder-32b-instruct', status: 'running' },
            { step: 'code_analysis', role: 'code_analysis', model: 'qwen/qwen-2.5-coder-32b-instruct', status: 'done', payload: { files_analyzed: 2, findings_count: 1 } },
          ],
          codeModel: 'qwen/qwen-2.5-coder-32b-instruct',
        })
      )
      assert(doneHtml.includes('COMPLETED'), 'Must show COMPLETED')
      assert(doneHtml.includes('2 files analyzed · 1 findings'), 'Must update detail with payload')
      console.log('✓ Scenario 6 passed')
    }

    // Scenario 7: Findings panel renders correctly and does not break issue review
    console.log('Testing Scenario 7: Findings panel alongside IssueCard without workflow breakage...')
    {
      const issue = {
        id: 'd1',
        original: {
          id: 'd1',
          title: 'Add type annotations to pipeline emitters',
          context: 'Improves maintainability and prevents runtime type errors.',
          files_to_touch: ['backend/pipeline.py'],
          acceptance_criteria: ['All emit calls typed', 'Mypy passes'],
          difficulty: 'beginner',
          source: 'todo',
        },
        judge: {
          score: 9,
          critique: 'Clear context and well-scoped for newcomers.',
          problems: [],
        },
        final: {
          id: 'd1',
          title: 'Add type annotations to pipeline emitters',
          context: 'Improves maintainability and prevents runtime type errors.',
          files_to_touch: ['backend/pipeline.py'],
          acceptance_criteria: ['All emit calls typed', 'Mypy passes'],
          difficulty: 'beginner',
          source: 'todo',
        },
        models_used: {
          drafter: 'nvidia/nemotron-4-340b-instruct',
          judge: 'nvidia/nemotron-nano-4b-instruct',
          rewrite: 'google/gemma-2-9b-it',
          code_analysis: 'qwen/qwen-2.5-coder-32b-instruct',
        },
      }

      const issueCardHtml = renderToStaticMarkup(
        React.createElement(IssueCard, {
          issue,
          onApprove: () => Promise.resolve('https://github.com/test/repo/issues/1'),
        })
      )

      assert(issueCardHtml.includes('Add type annotations to pipeline emitters'), 'IssueCard title rendered')
      assert(issueCardHtml.includes('Score:'), 'Score badge rendered')
      assert(issueCardHtml.includes('9/10'), 'Judge score rendered')
      assert(issueCardHtml.includes('Approve &amp; Post to GitHub') || issueCardHtml.includes('Approve & Post to GitHub'), 'Approval button preserved')
      assert(issueCardHtml.includes('qwen-2.5-coder-32b-instruct'), 'Code model tag displayed on IssueCard')
      console.log('✓ Scenario 7 passed')
    }

    // Scenario 8: Distinguishes between skipped, failed, empty findings, and in-progress states
    console.log('Testing Scenario 8: State distinction across all variations...')
    {
      // Skipped
      const skippedHtml = renderToStaticMarkup(React.createElement(CodeFindingsPanel, { codeModel: '', events: [] }))
      assert(skippedHtml.includes('Code analysis skipped because Qwen is not configured.'))

      // Failed
      const failedHtml = renderToStaticMarkup(React.createElement(CodeFindingsPanel, {
        codeModel: 'qwen/qwen-2.5-coder-32b-instruct',
        events: [{ step: 'code_analysis', status: 'error', detail: 'Timeout error' }]
      }))
      assert(failedHtml.includes('Code analysis failed.'))
      assert(failedHtml.includes('Timeout error'))

      // In progress
      const runningHtml = renderToStaticMarkup(React.createElement(CodeFindingsPanel, {
        codeModel: 'qwen/qwen-2.5-coder-32b-instruct',
        events: [{ step: 'code_analysis', status: 'running' }]
      }))
      assert(runningHtml.includes('Code analysis in progress...'))

      // Empty findings
      const emptyHtml = renderToStaticMarkup(React.createElement(CodeFindingsPanel, {
        codeModel: 'qwen/qwen-2.5-coder-32b-instruct',
        events: [{ step: 'code_analysis', status: 'done', payload: { findings: [] } }]
      }))
      assert(emptyHtml.includes('No code findings returned.'))

      // Not started
      const waitingHtml = renderToStaticMarkup(React.createElement(CodeFindingsPanel, {
        codeModel: 'qwen/qwen-2.5-coder-32b-instruct',
        events: []
      }))
      assert(waitingHtml.includes('Code analysis has not started.'))
      console.log('✓ Scenario 8 passed')
    }

    console.log('\n======================================================')
    console.log('ALL FRONTEND CODE REVIEWER VERIFICATION TESTS PASSED!')
    console.log('======================================================')
  } finally {
    await vite.close()
  }
}

runTests().catch((err) => {
  console.error('Test execution failed:', err)
  process.exit(1)
})
