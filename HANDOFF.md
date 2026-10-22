# KINDLING: Master Handoff for Antigravity CLI

Working name: **Kindling** (rename freely). Read this whole file, then PLAN FIRST. Do not write code until the plan is approved by me.

## 0. How to use this file
1. Put this file in the project root as `HANDOFF.md`.
2. Start Antigravity CLI in that folder and paste the "First message" from section 14.
3. The CLI must reply with a plan and file structure. I approve it, then it builds phase by phase, stopping after each phase.

## 1. Situation
- Event: Hacktoberfest hackathon at VU, 22 Oct 2026. Build starts 12:00. Submissions open 15:00 and close 16:00.
- Real build time: about 3 hours (12:00 to 15:00). Submit between 15:00 and 15:30. 15:30 to 16:00 is buffer only.
- Solo builder. Strengths: agents and tool-calling workflows, React/Node/Python.
- Chosen track: **Best Open-Source AI Project** (open-source or open-weight AI must be an important part of how the project works). Secondary: Best Use of Gemma 4, only if the rules allow entering both.
- Organizers recommend using any open-source model.
- Everything must be built during the event. No pre-written project code.

## 2. The product
A maintainer pastes a GitHub repo URL. A **crew of open-weight models, each with a visible role**, drafts contributor-ready GitHub issues, critiques them, rewrites them, and the maintainer approves each one before it posts to GitHub.

**The one thing judges must remember:** a crew of open models, each with a visible role. The UI centerpiece is a live pipeline view of the crew working.

Pitch lines:
- Open-Source AI track: "A pipeline of open-weight models, each with a clear job, that helps maintainers get more contributors. Self-hostable: change one env var and it runs on a local model."
- Gemma 4 track (secondary): "Gemma 4 reads a user's bug screenshot and turns it into a structured, well-scoped issue."

## 3. Hard constraints
- No auth, no database (JSON files only), no multi-repo support, no extra pages.
- Public-ready repo: MIT LICENSE, README, `.env.example`, `.gitignore` (never commit keys).
- Stack: Python 3.11 + FastAPI backend, React (Vite) frontend, `openai` Python SDK for all LLM calls.
- The demo runs on the NVIDIA hosted API for speed and reliability, but the code stays provider-agnostic: Ollama and LM Studio must work by changing env vars only. Only claim local support in the README if it has been tested once.

## 4. Model layer
One OpenAI-compatible client in `backend/llm.py`. Env vars: `LLM_BASE_URL`, `LLM_API_KEY`.

| Provider | Base URL |
|---|---|
| NVIDIA hosted | `https://integrate.api.nvidia.com/v1` |
| Ollama | `http://localhost:11434/v1` |
| LM Studio | `http://localhost:1234/v1` |

Roles (each has its own model env var; no hardcoded ids; placeholders in `.env.example`):

| Role | Env var | Job | Candidate models (VERIFY with list_models first) |
|---|---|---|---|
| Drafter | `DRAFTER_MODEL` | Writes issue drafts and does the rewrite pass | `nemotron-3-super-120b-a12b` |
| Judge | `JUDGE_MODEL` | Critiques drafts. MUST be a different model from the drafter | another open model that works on my key |
| Vision | `VISION_MODEL` | Turns a bug screenshot into an issue draft | `gemma-4-31b-it` (or `nemotron-nano-12b-v2-vl`) |
| Scanner (optional, lowest priority) | `SCANNER_MODEL` | Shortlists contribution opportunities | `nemotron-3-nano-30b-a3b` |

Rules:
- Each role has a one-line "why this model" string in config, shown in the UI. Judges will ask why each model is used.
- Do NOT rely on native tool-calling. Models return plain JSON, validated with pydantic, with one retry on invalid output.
- Some catalog models may not be callable on my account. `scripts/list_models.py` calls `GET /models` and runs one tiny test completion per configured model, so I know which actually work. This is the first script to build.

## 5. Pipeline
Every step emits an event: `{run_id, step, role, model, status, started_at, duration_ms, payload?}`.

1. **Scan (optional):** if `SCANNER_MODEL` is unset, skip it and give the drafter the repo summary directly.
2. **Draft:** up to 3 issues from the repo summary.
3. **Judge:** per draft, returns `{score 1-10, critique (2-3 lines)}`.
4. **Rewrite:** the drafter improves each draft using the critique. Keep the original draft too.

Run per-draft judge and rewrite calls in parallel. Cap at 3 issues so the demo stays fast.

### Draft schema
```json
{
  "id": "string",
  "title": "string",
  "context": "string",
  "files_to_touch": ["path"],
  "acceptance_criteria": ["string"],
  "difficulty": "beginner | intermediate",
  "source": "todo | open_issue | readme_gap | screenshot"
}
```
Each issue card holds: `original`, `judge {score, critique}`, `final`, and `models_used`.

## 6. GitHub tools (`github_tools.py`, REST API, `GITHUB_TOKEN`)
- Repo tree (cap about 200 files), README, open issues, grep for TODO/FIXME in a limited set of source files.
- Cap file sizes so the context stays small.
- Create an issue on `TARGET_REPO` (env var) so demo posting is safe.

## 7. API
- `POST /api/scan {repo_url}` returns `{run_id}` and starts the pipeline.
- `GET /api/stream/{run_id}` streams pipeline events (Server-Sent Events).
- `POST /api/approve {draft}` creates the issue on `TARGET_REPO` and returns the issue URL.
- `POST /api/screenshot` (stretch): image upload, then the vision model produces a draft in the same schema, flowing through judge and rewrite like the others.
- Caching: every finished run is saved to `data/cache/<owner>__<repo>.json`. `DEMO_MODE=cached` returns the cached run and replays the events with realistic delays, so the live view still animates with zero model calls. This is the safety net for rate limits and bad Wi-Fi.

## 8. Frontend (single page, clean and minimal)
- Top: repo URL input and Run button.
- **Centerpiece: live pipeline view.** One node per crew member showing role, model name, license note, the "why this model" line, status (waiting, running, done) and time taken. Nodes light up in order as events arrive.
- Below: one card per issue with three stages: Original draft, Judge critique with score, Final rewritten issue. Each card has an Approve button that posts the issue and shows the link.
- Footer: names the open-weight models used, with a note that the base URL can be switched to a local model.

## 9. File structure (proposed; the CLI may adjust)
```
kindling/
  backend/ main.py config.py llm.py github_tools.py pipeline.py schemas.py events.py
  frontend/ (Vite + React) src/App.jsx src/components/PipelineView.jsx src/components/IssueCard.jsx
  data/cache/
  scripts/ list_models.py seed_demo_repo.md
  .env.example  README.md  LICENSE  HANDOFF.md
```

## 10. Build phases and clock (stop after each phase and report)
| Time | Phase | Done when |
|---|---|---|
| 12:00-12:20 | P0 Setup: repo, MIT license, skeletons, model client, `list_models.py` | I know which models work on my key |
| 12:20-1:15 | P1 Backend CLI: GitHub tools plus Draft step | Running on the demo repo prints valid drafts |
| 1:15-1:45 | P2 Judge plus Rewrite | Each draft gets a critique, a score and a rewrite |
| 1:45-2:30 | P3 API, SSE, pipeline view, issue cards, Approve | End-to-end run in the browser; an issue lands on `TARGET_REPO` |
| 2:30-2:45 | P4 Cache and replay mode; screenshot feature only if time remains | Cached run replays with no model calls |
| 2:45-3:00 | P5 **FEATURE FREEZE.** README, screenshots, push to public repo | Repo is public, README complete |
| 3:00-3:30 | Record the demo video, submit | Submission confirmed |
| 3:30-4:00 | Buffer only | Do not start anything new |

## 11. Cut ladder (if behind, cut in this order)
1. Leaderboard (do not build at all).
2. Scanner step.
3. Screenshot (vision) feature.
4. Live animation (fall back to static role labels with timings).
5. Last resort: judge shows the score only (no rewrite).
Never cut: Draft, Judge, the pipeline view, Approve, the cache fallback.

## 12. Demo (90 seconds)
Demo target: a tiny demo repo created just for this, seeded with a small app, a README, a few TODO comments, 2-3 vague open issues and one UI bug I can screenshot. Say plainly that it is a demo repo. Keep one cached run on a real public repo to show it generalizes.

1. The problem: maintainers need contributors, and vague issues scare newcomers away.
2. Paste the repo URL and run it.
3. Watch the crew work in the pipeline view (name each model and its role).
4. Show an issue card: original draft, judge critique, rewritten issue.
5. Optional: drop in a bug screenshot and show the Gemma-generated issue.
6. Click Approve and show the issue live on GitHub.
7. Close by showing the env var that switches to a local model (only if tested).

## 13. README must include
One-paragraph pitch, screenshot of the pipeline view, model list with licenses and the reason for each, setup steps (env vars, run backend, run frontend), how to switch to Ollama or LM Studio, and the open-source license.

## 14. Submission checklist
- At 12:00, ask the organizers: can one project enter both tracks, what does a submission need (repo link, video, form), and is the video length limited?
- Public repo link works in a logged-out browser. No keys committed.
- Demo video recorded and uploaded as required.
- Submit between 15:00 and 15:30. Confirm the submission went through.

## 15. First message to paste into Antigravity CLI
```
Read HANDOFF.md fully. Do NOT write code yet. First reply with: (1) a short build plan, (2) the final file structure, (3) any risks or questions you have about the spec. Keep it short. After I approve, build one phase at a time (P0 to P5 in section 10), and after each phase tell me exactly how to run and test it, what is done, what is untested, and what you would cut if time is short. Priority if time is short: drafter, judge, rewrite, pipeline view, approve, cache fallback, then screenshot, then scanner.
```
