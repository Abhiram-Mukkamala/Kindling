# Graph Report - hacktober_Kindling  (2026-10-22)

## Corpus Check
- 29 files · ~25,154 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 4, .css 2, .example 1)

## Summary
- 248 nodes · 503 edges · 18 communities (11 shown, 7 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6d7cd3a3`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Pipeline Orchestration and Crew Execution
- Event Streaming and SSE Dispatch
- Frontend Dependencies and Tooling
- GitHub Ingestion and Issue Creation
- Configuration and Model Role Routing
- LLM Client and JSON Structured Parsing
- Graphify Knowledge Graph Integration
- Architecture Specifications and Project Strategy
- Oxlint Linter Configuration
- App.jsx
- Web Application Entry and Shell
- Python Environment and Dependency Packages
- Prompt Engineering and Model Templates
- UI Vector Icons Sprite
- Project Visual Hero Graphic
- React UI Framework Asset
- Vite Bundler Asset

## God Nodes (most connected - your core abstractions)
1. `Draft` - 19 edges
2. `TestModelRoutingAndPipeline` - 18 edges
3. `process_drafts()` - 17 edges
4. `run_pipeline()` - 15 edges
5. `draft_step()` - 12 edges
6. `JudgeResult` - 12 edges
7. `get_repo_summary()` - 11 edges
8. `get_graph_summary()` - 11 edges
9. `screenshot_scan()` - 11 edges
10. `code_analysis_step()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Backend Python Dependencies` --semantically_similar_to--> `Root Python Dependencies`  [INFERRED] [semantically similar]
  backend/requirements.txt → requirements.txt
- `Architecture Pipeline Diagram` --conceptually_related_to--> `Kindling Project Overview`  [INFERRED]
  docs/pipeline.png → README.md
- `main()` --calls--> `build_repo_summary()`  [EXTRACTED]
  scripts/run_cli.py → backend/github_tools.py
- `main()` --calls--> `draft_step()`  [EXTRACTED]
  scripts/run_cli.py → backend/pipeline.py
- `main()` --calls--> `process_drafts()`  [EXTRACTED]
  scripts/run_cli.py → backend/pipeline.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Kindling Crew Orchestration and Specification** — readme_open_weight_crew, handoff_role_model_mapping, docs_pipeline_diagram [INFERRED 0.85]

## Communities (18 total, 7 thin omitted)

### Community 0 - "Pipeline Orchestration and Crew Execution"
Cohesion: 0.08
Nodes (16): _get_model_for_role(), code_analysis_step(), judge_one(), process_drafts(), rewrite_one(), ScannerOutput, CodeAnalysisResult, CodeFinding (+8 more)

### Community 1 - "Event Streaming and SSE Dispatch"
Cohesion: 0.07
Nodes (16): make_emitter(), emit(), new_run(), approve_draft(), ApproveRequest, get_configuration(), get_graphify_summary_endpoint(), root() (+8 more)

### Community 2 - "Frontend Dependencies and Tooling"
Cohesion: 0.08
Nodes (24): dependencies, react, react-dom, devDependencies, oxlint, @types/react, @types/react-dom, vite (+16 more)

### Community 3 - "GitHub Ingestion and Issue Creation"
Cohesion: 0.16
Nodes (12): build_repo_summary(), create_issue(), create_issue_on_target_repo(), fetch_open_issues(), fetch_readme(), fetch_repo_tree(), fetch_source_files(), find_todos() (+4 more)

### Community 4 - "Configuration and Model Role Routing"
Cohesion: 0.13
Nodes (7): reload(), roles(), chat(), get_client(), _strip_thinking_tags(), main(), test_model()

### Community 5 - "LLM Client and JSON Structured Parsing"
Cohesion: 0.13
Nodes (8): chat_json(), extract_json(), _build_drafter_user_prompt(), draft_issues(), draft_step(), replay_cached(), run_pipeline(), scan_step()

### Community 6 - "Graphify Knowledge Graph Integration"
Cohesion: 0.22
Nodes (5): get_graph_context_for_files(), get_graph_summary(), main(), cli_emit(), main()

### Community 7 - "Architecture Specifications and Project Strategy"
Cohesion: 0.22
Nodes (7): Architecture Pipeline Diagram, Hackathon Master Handoff Spec, Role to Model Mapping Strategy, Deterministic Demo Replay Mode, Kindling Project Overview, Open-Weight Model Crew Architecture, Demo Repository Seeding Guide

### Community 8 - "Oxlint Linter Configuration"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 9 - "App.jsx"
Cohesion: 0.25
Nodes (6): App(), CodeFindingsPanel(), IssueCard(), PipelineView(), react, react-dom

### Community 10 - "Web Application Entry and Shell"
Cohesion: 0.67
Nodes (3): Frontend Single-Page Entry Shell, Kindling Flame Favicon, React Vite Frontend Spec

## Knowledge Gaps
- **14 isolated node(s):** `@types/react`, `@types/react-dom`, `oxlint`, `React Vite Frontend Spec`, `Kindling Flame Favicon` (+9 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 113 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Draft` connect `Pipeline Orchestration and Crew Execution` to `Event Streaming and SSE Dispatch`, `LLM Client and JSON Structured Parsing`, `Graphify Knowledge Graph Integration`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `Draft` (e.g. with `ApproveRequest` and `screenshot_scan()`) actually correct?**
  _`Draft` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `@types/react`, `@types/react-dom`, `oxlint` to the rest of the system?**
  _14 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Pipeline Orchestration and Crew Execution` be split into smaller, more focused modules?**
  _Cohesion score 0.07857142857142857 - nodes in this community are weakly interconnected._
- **Why does `TestModelRoutingAndPipeline` connect `Pipeline Orchestration and Crew Execution` to `Graphify Knowledge Graph Integration`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `TestModelRoutingAndPipeline` (e.g. with `CodeAnalysisResult` and `CodeFinding`) actually correct?**
  _`TestModelRoutingAndPipeline` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Should `Event Streaming and SSE Dispatch` be split into smaller, more focused modules?**
  _Cohesion score 0.07195121951219512 - nodes in this community are weakly interconnected._