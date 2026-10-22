import asyncio
import base64
import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend import config, prompts, llm
from backend.events import RUNS, new_run, make_emitter
from backend.github_tools import create_issue, build_repo_summary, parse_repo_url
from backend.pipeline import run_pipeline, process_drafts
from backend.schemas import Draft, RunResult

app = FastAPI(title="Kindling API", description="Open-Model Crew for Open-Source Contributor Issues")

# Enable CORS for local Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScanRequest(BaseModel):
    repo_url: str

class ApproveRequest(BaseModel):
    draft: Draft

@app.get("/")
async def root():
    """Root status endpoint directing visitors to frontend or interactive docs."""
    return {
        "name": "Kindling API",
        "status": "online",
        "frontend_url": "http://localhost:5173",
        "api_docs": "http://localhost:8000/docs",
        "endpoints": {
            "config": "/api/config",
            "scan": "/api/scan",
            "stream": "/api/stream/{run_id}",
            "approve": "/api/approve",
            "screenshot": "/api/screenshot",
        },
    }

@app.get("/api/config")
async def get_configuration():
    """Returns active crew configuration, assigned open models, target repo, and demo mode."""
    return {
        "roles": config.roles(),
        "target_repo": config.TARGET_REPO,
        "demo_mode": config.DEMO_MODE,
        "drafter_model": config.DRAFTER_MODEL,
        "judge_model": config.JUDGE_MODEL,
        "vision_model": config.VISION_MODEL,
        "scanner_model": config.SCANNER_MODEL,
    }

@app.post("/api/scan")
async def start_scan(request: ScanRequest):
    """Initiates an asynchronous repository scan run and returns run_id for SSE streaming."""
    repo_url = request.repo_url.strip()
    if not repo_url:
        raise HTTPException(status_code=400, detail="Repository URL is required.")

    try:
        parse_repo_url(repo_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    run_id = new_run(repo_url)
    asyncio.create_task(run_pipeline(run_id, repo_url))
    return {"run_id": run_id}

@app.get("/api/stream/{run_id}")
async def stream_run_events(run_id: str):
    """Streams pipeline events in real-time using Server-Sent Events (SSE)."""
    if run_id not in RUNS:
        raise HTTPException(status_code=404, detail="Run not found.")

    async def event_generator():
        last_index = 0
        while True:
            run_data = RUNS.get(run_id)
            if not run_data:
                break

            events = run_data["events"]
            while last_index < len(events):
                event = events[last_index]
                last_index += 1
                yield f"data: {json.dumps(event)}\n\n"

            if run_data.get("done", False) and last_index >= len(events):
                break

            await asyncio.sleep(0.1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

@app.post("/api/approve")
async def approve_draft(request: ApproveRequest):
    """Converts approved draft into a formatted GitHub issue and posts to TARGET_REPO."""
    draft = request.draft
    target = config.TARGET_REPO.strip()
    if not target or target == "owner/demo-repo":
        raise HTTPException(
            status_code=400,
            detail="TARGET_REPO is not configured in .env. Please set TARGET_REPO to a real repository you have access to.",
        )

    # Build rich Markdown issue description
    files_list = "\n".join(f"- `{f}`" for f in draft.files_to_touch) if draft.files_to_touch else "- *(No existing files touched)*"
    new_files_section = ""
    if getattr(draft, "new_files", None) and draft.new_files:
        new_files_list = "\n".join(f"- `{f}`" for f in draft.new_files)
        new_files_section = f"\n\n## New Files to Create\n{new_files_list}"

    criteria_list = "\n".join(f"- [ ] {ac}" for ac in draft.acceptance_criteria)

    markdown_body = f"""## Context
{draft.context}

## Files to Touch
{files_list}{new_files_section}

## Acceptance Criteria
{criteria_list}

---
*Difficulty: **{draft.difficulty.capitalize()}** | Source: **{draft.source}***
*Drafted by Kindling's open-model crew.*"""

    labels = ["good first issue"] if draft.difficulty == "beginner" else ["help wanted"]

    try:
        res = await create_issue(target, draft.title, markdown_body, labels=labels)
        return {"url": res.get("html_url", "")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/screenshot")
async def screenshot_scan(
    file: UploadFile = File(...),
    repo_url: Optional[str] = Form(None)
):
    """
    Multimodal Vision endpoint: converts a bug screenshot into a structured issue draft,
    then executes judge critique and rewrite passes.
    """
    if not config.VISION_MODEL:
        raise HTTPException(status_code=400, detail="VISION_MODEL is not configured in .env.")

    contents = await file.read()
    b64_img = base64.b64encode(contents).decode("utf-8")
    mime = file.content_type or "image/png"

    run_id = new_run(repo_url or "screenshot-upload")
    emit = make_emitter(run_id)

    async def vision_worker():
        try:
            tree: list[str] = []
            repo_summary = {"owner": "upload", "repo": "screenshot", "tree": [], "open_issues": [], "todos": []}
            if repo_url:
                try:
                    summary = await build_repo_summary(repo_url)
                    tree = summary.get("tree", [])
                    repo_summary = summary
                except Exception:
                    pass

            # Initial waiting states
            await emit({"step": "vision", "role": "vision", "model": config.VISION_MODEL, "status": "waiting"})
            await emit({"step": "judge", "role": "judge", "model": config.JUDGE_MODEL, "status": "waiting"})
            await emit({"step": "rewrite", "role": "drafter", "model": config.DRAFTER_MODEL, "status": "waiting"})

            # Step 1: Vision model analysis
            await emit({"step": "vision", "role": "vision", "model": config.VISION_MODEL, "status": "running"})
            user_text = "Here is a screenshot of a bug or UI issue.\n"
            if tree:
                user_text += f"Repository tree (only touch these files if relevant):\n" + "\n".join(tree[:100])
            else:
                user_text += "No repository tree provided. Leave files_to_touch empty."

            multimodal_user = [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64_img}"}},
            ]

            t0 = time.time()
            client = llm.get_client()
            response = await client.chat.completions.create(
                model=config.VISION_MODEL,
                messages=[
                    {"role": "system", "content": prompts.VISION_SYSTEM + "\nReturn ONLY JSON adhering to Draft schema."},
                    {"role": "user", "content": multimodal_user},
                ],
                max_tokens=2000,
                temperature=0.2,
            )
            v_dur = round((time.time() - t0) * 1000)
            raw = response.choices[0].message.content or ""
            parsed = llm.extract_json(raw)
            draft = Draft.model_validate(parsed)
            # Ensure id and source are set
            draft.id = "s1"
            draft.source = "screenshot"

            await emit({
                "step": "vision",
                "role": "vision",
                "model": config.VISION_MODEL,
                "status": "done",
                "duration_ms": v_dur,
            })

            # Step 2: Judge and Rewrite
            issues = await process_drafts([draft], repo_summary, emit)
            run_result = RunResult(repo=repo_url or "screenshot", issues=issues)
            result_dict = run_result.model_dump()
            RUNS[run_id]["result"] = result_dict

            await emit({
                "step": "final",
                "role": "system",
                "model": "Kindling",
                "status": "done",
                "payload": result_dict,
            })
            RUNS[run_id]["done"] = True

        except Exception as e:
            await emit({
                "step": "final",
                "role": "system",
                "model": "Kindling",
                "status": "error",
                "detail": str(e),
            })
            RUNS[run_id]["done"] = True

    asyncio.create_task(vision_worker())
    return {"run_id": run_id}

# Mount built frontend static files if dist/ exists
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

dist_dir = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if dist_dir.exists():
    app.mount("/assets", StaticFiles(directory=dist_dir / "assets"), name="assets")

    @app.get("/")
    async def serve_root():
        return FileResponse(dist_dir / "index.html")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Do not intercept API routes
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="Not Found")
        target_file = dist_dir / full_path
        if target_file.is_file():
            return FileResponse(target_file)
        return FileResponse(dist_dir / "index.html")

