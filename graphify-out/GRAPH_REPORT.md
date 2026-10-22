# Graph Report - hacktober_Kindling  (2026-10-22)

## Corpus Check
- Corpus is ~25,341 words - fits in a single context window. You may not need a graph.

## Summary
- 249 nodes · 504 edges · 18 communities (11 shown, 7 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16

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
- `Architecture Pipeline Diagram` --conceptually_related_to--> `Kindling Project Overview`  [INFERRED]
  docs/pipeline.png → README.md
- `Backend Python Dependencies` --semantically_similar_to--> `Root Python Dependencies`  [INFERRED] [semantically similar]
  backend/requirements.txt → requirements.txt
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

### Community 0 - "Community 0"
Cohesion: 0.08
Nodes (16): _get_model_for_role(), code_analysis_step(), judge_one(), process_drafts(), rewrite_one(), ScannerOutput, CodeAnalysisResult, CodeFinding (+8 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (16): make_emitter(), new_run(), approve_draft(), ApproveRequest, get_configuration(), get_graphify_summary_endpoint(), root(), ScanRequest (+8 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (24): dependencies, react, react-dom, devDependencies, oxlint, @types/react, @types/react-dom, vite (+16 more)

### Community 3 - "Community 3"
Cohesion: 0.16
Nodes (12): build_repo_summary(), create_issue(), create_issue_on_target_repo(), fetch_open_issues(), fetch_readme(), fetch_repo_tree(), fetch_source_files(), find_todos() (+4 more)

### Community 4 - "Community 4"
Cohesion: 0.13
Nodes (9): reload(), roles(), chat(), get_client(), _strip_thinking_tags(), main(), test_model(), cli_emit() (+1 more)

### Community 5 - "Community 5"
Cohesion: 0.15
Nodes (8): emit(), chat_json(), extract_json(), vision_worker(), _build_drafter_user_prompt(), draft_issues(), draft_step(), scan_step()

### Community 6 - "Community 6"
Cohesion: 0.23
Nodes (3): get_graph_context_for_files(), get_graph_summary(), main()

### Community 7 - "Community 7"
Cohesion: 0.22
Nodes (7): Architecture Pipeline Diagram, Hackathon Master Handoff Spec, Role to Model Mapping Strategy, Deterministic Demo Replay Mode, Kindling Project Overview, Open-Weight Model Crew Architecture, Demo Repository Seeding Guide

### Community 8 - "Community 8"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 9 - "Community 9"
Cohesion: 0.33
Nodes (6): scripts, build, dev, lint, preview, test

### Community 10 - "Community 10"
Cohesion: 0.67
Nodes (3): Frontend Single-Page Entry Shell, Kindling Flame Favicon, React Vite Frontend Spec

## Knowledge Gaps
- **14 isolated node(s):** `@types/react`, `@types/react-dom`, `oxlint`, `Kindling Prompt Catalog`, `Demo Repository Seeding Guide` (+9 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 114 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Draft` connect `Community 0` to `Community 1`, `Community 4`, `Community 5`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `Draft` (e.g. with `ApproveRequest` and `screenshot_scan()`) actually correct?**
  _`Draft` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `@types/react`, `@types/react-dom`, `oxlint` to the rest of the system?**
  _14 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.07857142857142857 - nodes in this community are weakly interconnected._
- **Why does `TestModelRoutingAndPipeline` connect `Community 0` to `Community 6`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `TestModelRoutingAndPipeline` (e.g. with `CodeAnalysisResult` and `CodeFinding`) actually correct?**
  _`TestModelRoutingAndPipeline` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.06976744186046512 - nodes in this community are weakly interconnected._