# Graph Report - hacktober_Kindling  (2026-10-22)

## Corpus Check
- 27 files · ~23,197 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 4, .css 2, .example 1)

## Summary
- 254 nodes · 485 edges · 14 communities (13 shown, 1 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 29 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4bf17c18`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- pipeline.py
- main.py
- package.json
- llm.py
- github_tools.py
- KINDLING: Master Handoff for Antigravity CLI
- draft_step
- KINDLING: Atomic Build Prompts for Antigravity CLI
- .oxlintrc.json
- scripts
- 🔥 Kindling
- Seed Demo Repo Guide
- React + Vite

## God Nodes (most connected - your core abstractions)
1. `Draft` - 19 edges
2. `process_drafts()` - 17 edges
3. `KINDLING: Master Handoff for Antigravity CLI` - 17 edges
4. `TestModelRoutingAndPipeline` - 16 edges
5. `run_pipeline()` - 15 edges
6. `draft_step()` - 12 edges
7. `JudgeResult` - 12 edges
8. `get_repo_summary()` - 11 edges
9. `screenshot_scan()` - 11 edges
10. `chat_json()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `✨ Key Features` --references--> `find_todos()`  [INFERRED]
  README.md → backend/github_tools.py
- `main()` --calls--> `build_repo_summary()`  [EXTRACTED]
  scripts/run_cli.py → backend/github_tools.py
- `main()` --calls--> `draft_step()`  [EXTRACTED]
  scripts/run_cli.py → backend/pipeline.py
- `main()` --calls--> `process_drafts()`  [EXTRACTED]
  scripts/run_cli.py → backend/pipeline.py
- `TestModelRoutingAndPipeline` --uses--> `Draft`  [INFERRED]
  tests/test_model_routing_and_pipeline.py → backend/schemas.py

## Import Cycles
- None detected.

## Communities (14 total, 1 thin omitted)

### Community 0 - "pipeline.py"
Cohesion: 0.09
Nodes (15): code_analysis_step(), judge_one(), process_drafts(), rewrite_one(), ScannerOutput, CodeAnalysisResult, CodeFinding, Draft (+7 more)

### Community 1 - "main.py"
Cohesion: 0.08
Nodes (14): make_emitter(), new_run(), approve_draft(), ApproveRequest, get_configuration(), root(), ScanRequest, screenshot_scan() (+6 more)

### Community 2 - "package.json"
Cohesion: 0.08
Nodes (24): dependencies, react, react-dom, devDependencies, oxlint, @types/react, @types/react-dom, vite (+16 more)

### Community 3 - "llm.py"
Cohesion: 0.12
Nodes (9): roles(), chat(), get_client(), _get_model_for_role(), _strip_thinking_tags(), main(), test_model(), cli_emit() (+1 more)

### Community 4 - "github_tools.py"
Cohesion: 0.16
Nodes (12): build_repo_summary(), create_issue(), create_issue_on_target_repo(), fetch_open_issues(), fetch_readme(), fetch_repo_tree(), fetch_source_files(), find_todos() (+4 more)

### Community 5 - "KINDLING: Master Handoff for Antigravity CLI"
Cohesion: 0.11
Nodes (18): 0. How to use this file, 10. Build phases and clock (stop after each phase and report), 11. Cut ladder (if behind, cut in this order), 12. Demo (90 seconds), 13. README must include, 14. Submission checklist, 15. First message to paste into Antigravity CLI, 1. Situation (+10 more)

### Community 6 - "draft_step"
Cohesion: 0.15
Nodes (8): emit(), chat_json(), extract_json(), vision_worker(), _build_drafter_user_prompt(), draft_issues(), draft_step(), scan_step()

### Community 7 - "KINDLING: Atomic Build Prompts for Antigravity CLI"
Cohesion: 0.20
Nodes (9): EMERGENCY PROMPTS (paste only if needed), GLOBAL RULES (paste first, once), KINDLING: Atomic Build Prompts for Antigravity CLI, P0: Setup (target 12:00 to 12:20), P1: GitHub tools and Draft step as a CLI (target 12:20 to 1:15), P2: Judge and Rewrite (target 1:15 to 1:45), P3: API, streaming, UI (target 1:45 to 2:30), P4: Cache replay and screenshot feature (target 2:30 to 2:45) (+1 more)

### Community 8 - ".oxlintrc.json"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 9 - "scripts"
Cohesion: 0.33
Nodes (6): scripts, build, dev, lint, preview, test

### Community 10 - "🔥 Kindling"
Cohesion: 0.33
Nodes (5): 1. Clone & Set Up Python Environment, ✨ Key Features, 🔥 Kindling, 🚀 Quick Start (Windows PowerShell), 🧠 The Open-Weight Model Crew

### Community 11 - "Seed Demo Repo Guide"
Cohesion: 0.40
Nodes (4): Recommended Demo Repo Structure, Recommended GitHub Issues to Create in Advance, Seed Demo Repo Guide, UI Bug for Screenshot Demo

### Community 12 - "React + Vite"
Cohesion: 0.50
Nodes (3): Expanding the Oxlint configuration, React Compiler, React + Vite

## Knowledge Gaps
- **3 isolated node(s):** `@types/react`, `@types/react-dom`, `oxlint`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 127 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Draft` connect `pipeline.py` to `main.py`, `llm.py`, `draft_step`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `Draft` (e.g. with `ApproveRequest` and `screenshot_scan()`) actually correct?**
  _`Draft` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `@types/react`, `@types/react-dom`, `oxlint` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `pipeline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08627450980392157 - nodes in this community are weakly interconnected._
- **Why does `find_todos()` connect `github_tools.py` to `🔥 Kindling`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `process_drafts()` (e.g. with `Draft` and `JudgeResult`) actually correct?**
  _`process_drafts()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07560975609756097 - nodes in this community are weakly interconnected._