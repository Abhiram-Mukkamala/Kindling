# 🔥 Kindling

**Kindling helps open-source maintainers get more contributors.** Three open-weight models, each with a visible role: one drafts contributor-ready GitHub issues, a different one critiques them, and the first rewrites them based on the critique. The maintainer sees every step live in a visual pipeline and approves each issue before anything posts to GitHub.

Built for the **GDGVU Hacktoberfest Hackathon** (Track: *Best Open-Source AI Project*).

---

## 🧠 The Open-Weight Model Crew

Kindling uses an OpenAI-compatible API layer (`AsyncOpenAI`) so every role is powered by open-weight models. By design, the **Judge** model must differ from the **Drafter** model so a model never grades its own homework.

| Role | Default Model | Why This Model | License |
| :--- | :--- | :--- | :--- |
| **Code Reviewer** | `qwen/qwen-2.5-coder-32b-instruct` | Deep source code analysis and line-level bug evidence extraction, augmented with Graphify AST call flows. | Apache 2.0 |
| **Drafter** | `nvidia/nemotron-3-ultra-550b-a55b` | High reasoning and code comprehension capacity for synthesizing repo trees, README gaps, and code context snippets into structured JSON issues without hallucinating identifiers. | NVIDIA Open Model License |
| **Judge (Critic)** | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` *(or `meta/muse-glimmer-30b`)* | Fast, independent reasoning model dedicated to auditing drafts for clarity, hallucinated symbols, missing acceptance criteria, and scope creep. | NVIDIA Open Model License / Open-Weight |
| **Quality Rewrite** | `google/gemma-4-31b-it` | Dedicated Gemma model to apply Judge critiques, polish acceptance criteria, and refine issue testability. | Gemma Terms of Use |
| **Vision (Stretch)** | `meta/llama-3.2-11b-vision-instruct` | Multimodal open-weight model capable of turning UI bug screenshots into structured contributor issues. | Llama 3.2 Community License |
| **Graphify Engine** | `Tree-sitter AST Extractor` | Deterministic local codebase knowledge graph (254 nodes, 485 edges) mapping call flows, module dependencies, and God Nodes. | Open-Source Tool |

---

## ✨ Key Features

- **Live Crew Pipeline UI:** Watch `GitHub Scanner` $\rightarrow$ `Drafter` $\rightarrow$ `Judge` $\rightarrow$ `Rewrite` execute in real time via Server-Sent Events (SSE), complete with model badges, role justifications, licenses, and execution durations.
- **Anti-Hallucination Guardrails:**
  - Comment-constrained `find_todos` extracts real `#`, `//`, `/*`, and `*` comments (ignoring strings and regexes) along with 5 lines of surrounding code context.
  - Strict prompt rules forbid inventing function, class, or test names not present in the inspected repo snippets.
  - Automatic path verification validates `files_to_touch` against the real GitHub repository tree while supporting newly proposed files via `new_files`.
- **Parallel Critique & Rewrite:** Per-draft Judge and Rewrite passes execute concurrently via `asyncio.gather` with capped token budgets (`max_tokens=1200`) for responsive turnaround.
- **Human-in-the-Loop Approval:** Maintainers inspect the **Original Draft**, **Judge Critique (with 1–10 score)**, and **Final Rewrite** side-by-side before clicking **Approve** to post directly to GitHub (with automatic 422 label-fallback retry).
- **Deterministic Demo Replay (`DEMO_MODE=cached`):** Every completed run saves its event stream and payload to `data/cache/<owner>__<repo>.json`. Switching to `cached` mode replays the exact SSE pipeline with realistic pacing and zero live API latency for stage demos.

---

## 🚀 Quick Start (Windows PowerShell)

### 1. Clone & Set Up Python Environment
```powershell
git clone [https://github.com/Abhiram-Mukkamala/Kindling.git](https://github.com/Abhiram-Mukkamala/Kindling.git)
cd Kindling
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
```

---

## 🏗️ System Architecture

This diagram shows Kindling's repository-analysis and issue-generation flow. **Graphify** executes deterministic AST parsing, producing a structural knowledge graph (254 nodes, 485 edges) that enriches **Qwen Coder** with call hierarchies and module dependencies, while providing an interactive visualization in the web UI.

```mermaid
flowchart TD
    User([Maintainer])

    subgraph Frontend["Frontend — React / Vite"]
        UI["Kindling UI"]
        PipelineView["Live Pipeline View"]
        IssueCards["Issue Cards and Review"]
        GraphViewer["Graphify Interactive Graph Viewer"]
    end

    subgraph GraphifyEngine["Graphify Knowledge Graph"]
        TreeSitter["Tree-sitter Deterministic AST Parser"]
        GraphArtifacts["Graphify Graph (254 nodes · 485 edges)"]
    end

    subgraph Backend["Backend — FastAPI"]
        API["API Routes"]
        Orchestrator["Pipeline Orchestrator"]
        GitHubIngestion["GitHub Repository Ingestion"]
        Scanner["Contribution Scanner — optional"]
        CodeAnalysis["Code Reviewer with AST Graph Context"]
        Qwen["Qwen Coder — CODE_MODEL"]
        Drafter["Nemotron Ultra — Drafter"]
        Judge["Nemotron Nano — Independent Judge"]
        Rewrite["Gemma — Quality Rewrite"]
    end

    GitHub["GitHub API"]
    ModelAPI["OpenAI-compatible Model API"]

    User --> UI
    UI <--> API
    API --> Orchestrator
    Orchestrator --> GitHubIngestion
    GitHubIngestion <--> GitHub

    TreeSitter --> GraphArtifacts
    GraphArtifacts --> CodeAnalysis
    GraphArtifacts --> API
    API --> GraphViewer
    GraphViewer --> UI

    Orchestrator --> Scanner
    Scanner --> Drafter

    Orchestrator --> CodeAnalysis
    CodeAnalysis --> Qwen
    Qwen --> Drafter

    GitHubIngestion --> Drafter
    Drafter --> Judge
    Judge --> Rewrite

    Drafter --> ModelAPI
    Judge --> ModelAPI
    Rewrite --> ModelAPI
    Qwen --> ModelAPI

    Orchestrator --> API
    API --> PipelineView
    API --> IssueCards
    PipelineView --> UI
    IssueCards --> UI
```
