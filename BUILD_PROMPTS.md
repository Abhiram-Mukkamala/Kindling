# KINDLING: Atomic Build Prompts for Antigravity CLI

Use with HANDOFF.md. Paste the GLOBAL RULES once at the start of the session, then paste ONE phase prompt at a time. Test each phase before sending the next.

---

## GLOBAL RULES (paste first, once)

```
You are building "Kindling" from HANDOFF.md. Follow these rules for the whole session:
1. Build ONLY the phase I name. When it is done, STOP and report: what is done, how to run and test it (exact commands), what is untested, what you would cut if time is short.
2. Do not add features, files, dependencies, auth, databases, or abstractions that the phase prompt does not list.
3. Do not run git commands. I commit myself.
4. Never hardcode model ids, API keys, or URLs. Everything comes from environment variables loaded with python-dotenv.
5. All LLM output is plain JSON validated with pydantic. Never rely on native tool-calling.
6. If anything in a prompt is ambiguous or a call fails in a way you cannot explain, tell me instead of inventing a workaround.
7. Keep code simple and readable. Comments only where logic is not obvious.
8. Python 3.11, FastAPI, pydantic v2, openai SDK (AsyncOpenAI), httpx. Frontend: Vite + React (JavaScript), no UI library, plain CSS.
Reply "ready" and wait.
```

---

## P0: Setup (target 12:00 to 12:20)

```
PHASE P0 ONLY. Create exactly this structure and contents, then stop.

ROOT FILES
- LICENSE: MIT, copyright holder "Kindling contributors", year 2026.
- .gitignore: .env, __pycache__/, *.pyc, .venv/, node_modules/, dist/, data/cache/*.json (keep data/cache/.gitkeep).
- .env.example with these keys and placeholder values, each with a one-line comment:
  LLM_BASE_URL=https://integrate.api.nvidia.com/v1
  LLM_API_KEY=your_key_here
  DRAFTER_MODEL=
  JUDGE_MODEL=
  VISION_MODEL=
  SCANNER_MODEL=            (optional; empty means skip the scan step)
  DRAFTER_WHY=Strong reasoning model that writes and rewrites issues
  JUDGE_WHY=Different model family from the drafter, so it does not grade its own work
  VISION_WHY=Multimodal Gemma 4 model that reads bug screenshots
  SCANNER_WHY=Small fast model that shortlists opportunities
  DRAFTER_LICENSE=open-weight (check model card)
  JUDGE_LICENSE=open-weight (check model card)
  VISION_LICENSE=open-weight (check model card)
  SCANNER_LICENSE=open-weight (check model card)
  GITHUB_TOKEN=
  TARGET_REPO=owner/demo-repo
  DEMO_MODE=live            (live or cached)
- README.md: just the title "Kindling" and one line: "Open-model crew that turns repos into contributor-ready issues." (final README is written in P5).

BACKEND (package folder backend/ with empty __init__.py)
- backend/requirements.txt: fastapi, uvicorn[standard], openai, httpx, pydantic, python-dotenv, python-multipart.
- backend/config.py: load .env, expose a Settings object (pydantic BaseModel or dataclass) with all env vars above. Helper roles() returns a list of dicts [{role, model, why, license}] for roles whose model env var is non-empty (roles: scanner, drafter, judge, vision).
- backend/llm.py:
  - get_client() returns a cached AsyncOpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY, timeout=90).
  - async def chat(role: str, messages: list[dict], max_tokens: int = 2000, temperature: float = 0.3) -> tuple[str, int]: picks the model for the role from settings, calls chat.completions.create, returns (text, duration_ms). Strip any <think>...</think> block from the text before returning.
  - def extract_json(text: str) -> dict: strip ``` fences, take the substring from the first "{" to the last "}", json.loads it. Raise ValueError if it fails.
  - async def chat_json(role: str, system: str, user: str, schema: type[BaseModel], max_tokens: int = 2000) -> tuple[BaseModel, int]: calls chat() with a system and user message, extracts JSON, validates with the pydantic schema. On failure retry ONCE, appending the user message: "Your last reply was not valid JSON for the schema. Return ONLY the JSON object, no prose." Returns (validated_model, total_duration_ms). Raise on second failure.
- scripts/list_models.py: standalone script (adds repo root to sys.path). Step 1: GET {LLM_BASE_URL}/models with the Authorization header and print the number of models returned. Step 2: for each configured role model, send a tiny chat completion ("Reply with the single word: ok", max_tokens 20), and print one line per role: role, model id, OK or FAILED with the error, and latency in ms. Exit code 0 even on failures.

Create data/cache/.gitkeep. Do not create frontend yet. Stop and report.
TEST: I will create .env, run `pip install -r backend/requirements.txt` then `python scripts/list_models.py`.
```

---

## P1: GitHub tools and Draft step as a CLI (target 12:20 to 1:15)

```
PHASE P1 ONLY.

backend/schemas.py (pydantic v2):
- class Draft: id: str, title: str, context: str, files_to_touch: list[str], acceptance_criteria: list[str], difficulty: Literal["beginner","intermediate"], source: Literal["todo","open_issue","readme_gap","screenshot"].
- class DraftList: drafts: list[Draft] (max 3 enforced by a validator that truncates to 3).
- class JudgeResult: score: int (1..10), critique: str, problems: list[str] = [].
- class IssueResult: id: str, original: Draft, judge: JudgeResult | None, final: Draft | None, models_used: dict[str,str].
- class RunResult: repo: str, issues: list[IssueResult].

backend/github_tools.py (httpx.AsyncClient, header "Authorization: Bearer {GITHUB_TOKEN}", "Accept: application/vnd.github+json"):
- parse_repo_url(url) -> (owner, repo). Accept https://github.com/owner/repo(.git)(/...) and "owner/repo".
- async get_repo_meta(owner, repo) -> dict with name, description, default_branch (GET /repos/{o}/{r}).
- async get_tree(owner, repo, branch) -> list[str] of file paths (GET /repos/{o}/{r}/git/trees/{branch}?recursive=1, only type=="blob"). Skip paths containing node_modules, dist/, build/, .git/, vendor/, __pycache__, and files ending .lock, .png, .jpg, .jpeg, .gif, .svg, .ico, .pdf, .zip, .min.js. Cap at 200 paths, prefer shorter paths first.
- async get_readme(owner, repo) -> str (GET /repos/{o}/{r}/readme, base64-decode content, return first 6000 characters, empty string if 404).
- async get_open_issues(owner, repo) -> list[dict] up to 15 of {number, title, body (first 500 chars), labels}. Exclude items that have a "pull_request" key.
- async get_file(owner, repo, path, branch) -> str (GET /repos/{o}/{r}/contents/{path}?ref=branch, base64-decode, return "" if larger than 20000 bytes or on any error).
- async find_todos(owner, repo, branch, paths) -> list[dict] up to 20 of {path, line, text}: fetch up to 15 code files (extensions .py .js .jsx .ts .tsx .java .go .rs .c .cpp .rb .php), concurrency limit 5 via asyncio.Semaphore, find lines containing TODO or FIXME, text trimmed to 200 chars.
- async build_repo_summary(repo_url) -> dict {owner, repo, description, default_branch, tree, readme, open_issues, todos}.
- async create_issue(target_repo, title, body, labels) -> dict with html_url (POST /repos/{target}/issues). If GitHub returns 422 and labels were sent, retry once without labels. Raise a clear error on other failures.

backend/prompts.py: module-level string constants:
DRAFTER_SYSTEM = """You are the Drafter in Kindling, a tool that helps open-source maintainers attract contributors. Given a repository summary, write up to 3 contributor-ready GitHub issues that a newcomer could finish in 1 to 3 hours.
Rules:
- Every path in files_to_touch MUST appear in the provided file tree. Never invent paths.
- Titles are specific and action-oriented (under 80 characters).
- context explains why the change matters and where to look, in 2 to 4 sentences.
- acceptance_criteria are 3 to 5 concrete, testable checks.
- difficulty is "beginner" or "intermediate".
- source is "todo", "open_issue", or "readme_gap" depending on where the idea came from.
- id is a short unique string like "d1", "d2", "d3".
Return ONLY a JSON object: {"drafts":[{"id","title","context","files_to_touch","acceptance_criteria","difficulty","source"}]}. No prose."""
JUDGE_SYSTEM = """You are the Judge in Kindling. You review ONE draft GitHub issue for a newcomer-friendly open-source repo. Score 1 to 10 on: clarity of the title and context, scope fits 1 to 3 hours for a newcomer, every file in files_to_touch exists in the provided file tree, acceptance criteria are specific and testable. Be strict and concrete.
Return ONLY a JSON object: {"score": <int 1-10>, "critique": "<2 to 3 sentences naming the biggest weaknesses>", "problems": ["<short problem>", ...]}. No prose."""
REWRITE_SYSTEM = """You are the Drafter rewriting an issue after the Judge's critique. Fix every weakness named in the critique. Keep paths limited to the provided file tree. Keep the same id and source.
Return ONLY the JSON object of one draft: {"id","title","context","files_to_touch","acceptance_criteria","difficulty","source"}. No prose."""
VISION_SYSTEM = """You are the Vision model in Kindling. Look at the screenshot of a bug or UI problem and write ONE contributor-ready GitHub issue about it. Use only file paths from the provided tree if one is given, otherwise leave files_to_touch empty. source must be "screenshot", id "s1".
Return ONLY a JSON object of one draft: {"id","title","context","files_to_touch","acceptance_criteria","difficulty","source"}. No prose."""
SCANNER_SYSTEM = """You are the Scanner in Kindling. From the repository summary, list up to 6 short contribution opportunities (one sentence each) that a newcomer could tackle. Return ONLY: {"opportunities":["...", ...]}."""

backend/pipeline.py (P1 portion only):
- async def draft_step(summary: dict) -> tuple[list[Draft], int]: build a user message containing description, file tree, README, open issues, and TODOs (as compact text, not raw JSON dumps of everything), call chat_json("drafter", DRAFTER_SYSTEM, user, DraftList), return (drafts, duration_ms).

scripts/run_cli.py: usage `python scripts/run_cli.py <repo_url>`. Builds the summary, runs draft_step, and prints each draft as pretty JSON plus the duration. Print a clear error if any file path in a draft is not in the tree (as a warning, do not crash).

Stop and report.
TEST: `python scripts/run_cli.py https://github.com/<me>/<demo-repo>` prints 1 to 3 valid drafts with real file paths.
```

---

## P2: Judge and Rewrite (target 1:15 to 1:45)

```
PHASE P2 ONLY. Extend backend/pipeline.py and scripts/run_cli.py.

In backend/pipeline.py add:
- async def judge_one(draft: Draft, tree: list[str]) -> tuple[JudgeResult, int]: user message = the draft as JSON plus the file tree; call chat_json("judge", JUDGE_SYSTEM, user, JudgeResult).
- async def rewrite_one(draft: Draft, judge: JudgeResult, summary: dict) -> tuple[Draft, int]: user message = original draft JSON, the critique and problems, and the file tree; call chat_json("drafter", REWRITE_SYSTEM, user, Draft).
- async def process_drafts(drafts: list[Draft], summary: dict, emit) -> list[IssueResult]: 
  1. emit({"step":"judge","role":"judge","status":"running"})
  2. run judge_one for all drafts in parallel with asyncio.gather(return_exceptions=True). If a judge call fails for a draft, set judge=None for that draft and continue.
  3. emit judge "done" with duration_ms = wall-clock time of the whole step and payload {"scores": [..]}.
  4. emit({"step":"rewrite","role":"drafter","status":"running"})
  5. run rewrite_one in parallel only for drafts with a judge result; if a rewrite fails, final = original.
  6. emit rewrite "done" with wall-clock duration_ms.
  7. return IssueResult list with models_used = {"drafter": DRAFTER_MODEL, "judge": JUDGE_MODEL}.
- emit is an async callable taking a dict; in the CLI it prints one line per event.

Update scripts/run_cli.py: after draft_step, call process_drafts and print for each issue: ORIGINAL title, JUDGE score and critique, FINAL title.

Stop and report.
TEST: running the CLI shows, for each draft, an original title, a score with critique, and a visibly improved final version. Judge and drafter must be different models (warn in the console if JUDGE_MODEL == DRAFTER_MODEL).
```

---

## P3: API, streaming, UI (target 1:45 to 2:30)

```
PHASE P3 ONLY. Backend API first, then frontend. Stop after both and report.

BACKEND: backend/events.py
- RUNS: dict[str, dict] in memory, each {"events": [], "done": False, "result": None, "repo": str}.
- def new_run(repo) -> run_id (uuid4 hex first 8).
- def make_emitter(run_id) -> async emit(event: dict): adds run_id, seq (len of events), started_at (ISO), stores in RUNS[run_id]["events"].
- Event shape: {run_id, seq, step, role, model, status ("waiting"|"running"|"done"|"error"), started_at, duration_ms (optional), detail (optional short string), payload (optional)}.

BACKEND: backend/pipeline.py add
- async def run_pipeline(run_id, repo_url): 
  1. Get emit. Emit "waiting" events for every configured role/step in order (scanner if SCANNER_MODEL set, then drafter, judge, rewrite), each with the model name.
  2. If DEMO_MODE == "cached" and data/cache/<owner>__<repo>.json exists: load it and call replay_cached(...) (see P4), then return. (If P4 is not built yet, skip this branch.)
  3. Otherwise: build_repo_summary; emit github step "done" with detail "N files, M issues, K TODOs"; if scanner configured run it (P4+), then emit drafter "running", draft_step, emit drafter "done" with duration_ms; then process_drafts.
  4. Build RunResult, store in RUNS[run_id]["result"], save to data/cache/<owner>__<repo>.json as {"events": [...], "result": ...}, emit {"step":"final","status":"done","payload": result}, set done=True.
  5. Wrap everything in try/except: on error emit {"step":"final","status":"error","detail": str(e)} and set done=True.

BACKEND: backend/main.py (FastAPI)
- CORS allow all origins (hackathon demo).
- GET /api/config -> {"roles": roles(), "target_repo": TARGET_REPO, "demo_mode": DEMO_MODE}.
- POST /api/scan {repo_url} -> creates run, starts run_pipeline with asyncio.create_task, returns {"run_id"}.
- GET /api/stream/{run_id}: StreamingResponse with media_type "text/event-stream". Generator keeps an index, yields "data: <json>\n\n" for every new event in RUNS[run_id]["events"], sleeps 0.1s when none, ends once done and all events are sent. Late subscribers get all events from the start.
- POST /api/approve {draft: Draft} -> builds a markdown body ("## Context", "## Files to touch" bullet list in backticks, "## Acceptance criteria" as "- [ ]" checklist, plus a footer "Drafted by Kindling's open-model crew"), labels = ["good first issue"] if difficulty == "beginner" else [], calls create_issue(TARGET_REPO, ...), returns {"url": html_url}.
- Run command: `uvicorn backend.main:app --reload --port 8000` from the repo root.

FRONTEND (create with `npm create vite@latest frontend -- --template react`, then edit)
- vite.config.js: proxy "/api" to http://localhost:8000.
- src/App.jsx state: repoUrl, config, events (array), result, running. On load fetch /api/config.
- startRun(): POST /api/scan, get run_id, open new EventSource(`/api/stream/${run_id}`), append each parsed event to state; when step === "final" close the EventSource and set result (status "done") or show an error banner (status "error").
- src/components/PipelineView.jsx: props {roles, events}. Render one node per entry in a fixed order: github, scanner (only if in roles), drafter, judge, rewrite. Each node shows: role label, model name, "why this model" text, license note, a status chip (waiting grey, running amber with pulse animation, done green, error red), and duration (formatted like 4.2s) when done. Status for a node = status of its latest event. Draw simple connector arrows between nodes (CSS). This is the centerpiece: place it directly under the input, large and clear.
- src/components/IssueCard.jsx: props {issue, onApprove}. Header with title and a score badge (green >=8, amber 5-7, red <5). Three tabs: "Original", "Judge critique", "Final". Each draft view shows context, files (as code chips), acceptance criteria (list), difficulty tag. Judge tab shows score, critique, problems. Footer: model badges ("Drafter: X", "Judge: Y") and an Approve button that calls POST /api/approve with the FINAL draft, then shows "Posted" with a link to the returned url; button disabled after success; show errors inline.
- src/index.css: clean dark theme, system font, max-width 960px centered, readable spacing. Footer text: "Built with open-weight models: <model list>. Swap LLM_BASE_URL to run locally."
- Frontend run: `cd frontend && npm install && npm run dev`.

Stop and report.
TEST: start both servers, paste the demo repo URL, watch the pipeline nodes turn amber then green in order, see issue cards with all three tabs, click Approve and confirm the issue appears in TARGET_REPO on GitHub.
```

---

## P4: Cache replay and screenshot feature (target 2:30 to 2:45)

```
PHASE P4 ONLY.

1. Cache replay. In backend/pipeline.py add async def replay_cached(run_id, cache): iterate the saved events in order; for each, wait min(max(event.duration_ms/1000 * 0.6, 0.4), 3.0) seconds before emitting it (re-emit with the new run_id), so the live pipeline view animates without any model call. Then set RUNS[run_id]["result"] and done=True. Verify the cache branch in run_pipeline works when DEMO_MODE=cached.

2. Screenshot feature.
- POST /api/screenshot (multipart: file UploadFile, repo_url optional str). Reads the image, base64-encodes it, builds a user message in OpenAI vision format: content = [{"type":"text","text": <short context + file tree if repo_url given>}, {"type":"image_url","image_url":{"url":"data:<mime>;base64,<b64>"}}], calls chat_json("vision", VISION_SYSTEM, ...) with Draft as the schema, then runs the result through process_drafts so it gets judged and rewritten. Returns {"run_id"} and streams events like /api/scan (steps: vision, judge, rewrite).
- If the model rejects the image_url format, return a clear error and tell me; do not invent a workaround.
- Frontend: add an "Add a bug screenshot" file input under the repo input with a "Draft from screenshot" button that calls the endpoint and reuses the same stream and card rendering. Add a "vision" node to PipelineView only when a screenshot run is active.

3. Optional Scanner (ONLY if SCANNER_MODEL is set): async def scan_step(summary) -> (list[str], int) using SCANNER_SYSTEM; pass the opportunities into the drafter's user message as a "Suggested focus" section.

Stop and report.
TEST: set DEMO_MODE=cached and run the demo repo: it replays in a few seconds with zero model calls. Upload a bug screenshot: a draft appears with a critique and a rewrite.
```

---

## P5: Freeze, README, publish (target 2:45 to 3:00)

```
PHASE P5 ONLY. Feature freeze: add NO new features.

1. Write the final README.md: one-paragraph pitch ("Kindling helps open-source maintainers attract contributors using a crew of open-weight models..."), a "How it works" section listing each role, its model and why (read the "why" and license text from .env.example), setup steps (clone, create .env from .env.example, `pip install -r backend/requirements.txt`, `uvicorn backend.main:app --port 8000`, `cd frontend && npm install && npm run dev`), a "Run on a local model" section (set LLM_BASE_URL to the Ollama or LM Studio URL and set the model env vars to local model names), a "Demo mode" section explaining DEMO_MODE=cached, a screenshot placeholder `docs/pipeline.png`, and the MIT license note.
2. Security check: confirm .env is gitignored, no keys appear anywhere in the code, .env.example only has placeholders. List what you checked.
3. Remove dead code and unused imports. Do not refactor.
4. Print the final `git status`-style list of files that should be committed (do not run git).

Stop and report.
```

---

## EMERGENCY PROMPTS (paste only if needed)

Behind schedule (apply the cut ladder):
```
We are behind. Cut in this order and tell me what you removed: scanner, screenshot feature, live animation (show static role labels with durations), and finally the rewrite pass (judge shows score only). Do NOT cut Draft, Judge, the pipeline view, Approve, or the cache fallback.
```

A model call fails or is too slow:
```
The model for role <ROLE> is failing or slow. Do not change any code. Tell me the exact env var to change in .env, and make sure the code reads the model from that env var only.
```

Output is not valid JSON:
```
Model output for role <ROLE> is not parsing. Show me the raw model output for one failing call (log it to the console), then improve extract_json and the retry message. Do not change the schema.
```
