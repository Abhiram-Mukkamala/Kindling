import asyncio
import json
import time
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional, Callable, Awaitable
from pydantic import BaseModel, Field

from backend import config, llm, prompts
from backend.graphify_tools import get_graph_context_for_files
from backend.github_tools import build_repo_summary, parse_repo_url, get_repo_summary
from backend.schemas import (
    Draft,
    DraftList,
    JudgeResult,
    IssueResult,
    RunResult,
    IssueDraft,
    DraftsBatch,
    CodeFinding,
    CodeAnalysisResult,
)
from backend.events import RUNS, make_emitter

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

class ScannerOutput(BaseModel):
    opportunities: List[str] = Field(default_factory=list)

def _build_drafter_user_prompt(
    summary: Dict[str, Any],
    opportunities: Optional[List[str]] = None,
    code_findings: Optional[List[CodeFinding]] = None,
) -> str:
    parts = [
        f"Repository: {summary.get('owner', '')}/{summary.get('repo', '')}",
        f"Description: {summary.get('description', '')}",
        f"Default Branch: {summary.get('default_branch', 'main')}",
        "",
        "=== REPOSITORY FILE TREE (Only use paths listed here) ===",
        "\n".join(summary.get("tree", [])[:150]),
        "",
        "=== README EXCERPT ===",
        summary.get("readme", "")[:2500] if summary.get("readme") else "No README available.",
        "",
        "=== OPEN ISSUES SAMPLE ===",
    ]
    issues = summary.get("open_issues", [])
    if issues:
        for it in issues[:8]:
            lbls = it.get('labels', [])
            lbl_str = f" (Labels: {', '.join(lbls)})" if lbls else ""
            num_str = f"#{it['number']}: " if 'number' in it else ""
            parts.append(f"{num_str}{it['title']}{lbl_str}\n{it.get('body', '')[:200]}\n")
    else:
        parts.append("No open issues.")

    parts.append("=== CODE TODO/FIXME COMMENTS ===")
    todos = summary.get("todos", [])
    if todos:
        for td in todos[:12]:
            tag = td.get('tag', 'TODO')
            file_p = td.get('path') or td.get('file', '')
            content = td.get('text') or td.get('content', '')
            parts.append(f"[{tag}] {file_p}:{td.get('line', '')} -> {content}")
            snippet = td.get('snippet')
            if snippet:
                parts.append("Context Snippet (surrounding code):")
                parts.append(snippet)
                parts.append("")
    else:
        parts.append("No explicit TODO comments found.")

    if code_findings:
        parts.append("\n=== VERIFIED CODE REVIEW FINDINGS (with source evidence) ===")
        for f in code_findings:
            line_str = f" (Lines: {f.line_range})" if f.line_range else ""
            parts.append(f"- [{f.severity.upper()}] {f.file_path}{line_str}: {f.explanation}")
            if f.evidence:
                parts.append(f"  Evidence: \"{f.evidence}\"")

    if opportunities:
        parts.append("\n=== SUGGESTED CONTRIBUTION OPPORTUNITIES ===")
        for op in opportunities:
            parts.append(f"- {op}")

    parts.append("\nWrite up to 3 contributor-ready issues adhering to the rules.")
    return "\n".join(parts)

async def scan_step(summary: Dict[str, Any]) -> Tuple[List[str], int]:
    """Generates a quick shortlist of contribution opportunities using the Scanner model."""
    user_prompt = (
        f"Repository: {summary['owner']}/{summary['repo']}\n"
        f"Description: {summary.get('description', '')}\n"
        f"README excerpt:\n{summary.get('readme', '')[:1500]}\n"
        f"Files:\n" + "\n".join(summary.get("tree", [])[:60])
    )
    result, duration_ms = await llm.chat_json("scanner", prompts.SCANNER_SYSTEM, user_prompt, ScannerOutput, max_tokens=1000)
    return result.opportunities, duration_ms

async def code_analysis_step(summary: Dict[str, Any]) -> Tuple[List[CodeFinding], int]:
    """
    Analyzes real source code files from the repository using the CODE_MODEL (Qwen).
    Augments prompt with Graphify AST call-graph dependencies when available.
    Gracefully handles empty repositories or no eligible files.
    """
    source_files = summary.get("source_files", {})
    if not source_files:
        return [], 0

    files_text_blocks = []
    for fpath, code in source_files.items():
        files_text_blocks.append(f"=== FILE: {fpath} ===\n{code}\n")

    graph_context = get_graph_context_for_files(list(source_files.keys()))
    prompt_parts = [
        f"Repository: {summary.get('owner', '')}/{summary.get('repo', '')}",
    ]
    if graph_context:
        prompt_parts.append(f"{graph_context}\n")

    prompt_parts.append(
        "Review the following source files for concrete bugs, edge cases, or code smells:\n\n"
        + "\n".join(files_text_blocks)
    )

    user_prompt = "\n\n".join(prompt_parts)

    result, duration_ms = await llm.chat_json(
        "code_analysis",
        prompts.CODE_ANALYSIS_SYSTEM,
        user_prompt,
        CodeAnalysisResult,
        max_tokens=1500,
    )
    return result.findings, duration_ms

async def draft_step(
    summary: Dict[str, Any],
    opportunities: Optional[List[str]] = None,
    code_findings: Optional[List[CodeFinding]] = None,
) -> Tuple[List[Draft], int]:
    """Generates up to 3 structured issue drafts using the Drafter model."""
    user_prompt = _build_drafter_user_prompt(summary, opportunities, code_findings)
    result, duration_ms = await llm.chat_json("drafter", prompts.DRAFTER_SYSTEM, user_prompt, DraftList, max_tokens=3000)
    return result.drafts, duration_ms

async def draft_issues(repo_summary: Dict[str, Any]) -> List[IssueDraft]:
    """Backwards compatibility alias for draft_step."""
    drafts, _ = await draft_step(repo_summary)
    return drafts

async def judge_one(draft: Draft, tree: List[str]) -> Tuple[JudgeResult, int]:
    """Runs quality evaluation on a single draft using the Judge model."""
    user_prompt = (
        f"Repository File Tree:\n" + "\n".join(tree[:150]) + "\n\n"
        f"Draft to review:\n"
        f"{draft.model_dump_json(indent=2)}"
    )
    result, duration_ms = await llm.chat_json("judge", prompts.JUDGE_SYSTEM, user_prompt, JudgeResult, max_tokens=1200)
    print(f"   [Judge Model] '{draft.title[:35]}...' -> {duration_ms}ms (Score: {result.score}/10)")
    return result, duration_ms

async def rewrite_one(draft: Draft, judge: JudgeResult, tree: List[str]) -> Tuple[Draft, int]:
    """
    Rewrites and polishes an issue draft incorporating Judge critique using the REWRITE_MODEL (Gemma).
    Preserves original draft if rewriting fails.
    """
    user_prompt = (
        f"Repository File Tree:\n" + "\n".join(tree[:150]) + "\n\n"
        f"Original Draft:\n{draft.model_dump_json(indent=2)}\n\n"
        f"Judge Score: {judge.score}/10\n"
        f"Judge Critique: {judge.critique}\n"
        f"Identified Problems:\n" + "\n".join(f"- {p}" for p in judge.problems)
    )
    result, duration_ms = await llm.chat_json("rewrite", prompts.REWRITE_SYSTEM, user_prompt, Draft, max_tokens=1200)
    print(f"   [Rewrite Model] '{draft.title[:35]}...' -> {duration_ms}ms")
    return result, duration_ms

async def process_drafts(
    drafts: List[Draft],
    summary: Dict[str, Any],
    emit: Callable[[Dict[str, Any]], Awaitable[None]],
    code_model_used: bool = False,
) -> List[IssueResult]:
    """
    Executes parallel Judge evaluation followed by parallel Rewrite using dedicated models.
    Emits pipeline events for each phase with exact model metadata.
    """
    tree = summary.get("tree", [])
    rewrite_model_id = config.REWRITE_MODEL or config.DRAFTER_MODEL

    # Step 1: Judge Phase
    await emit({
        "step": "judge",
        "role": "judge",
        "model": config.JUDGE_MODEL,
        "status": "running",
    })
    t_judge_start = time.time()
    judge_tasks = [judge_one(d, tree) for d in drafts]
    judge_outcomes = await asyncio.gather(*judge_tasks, return_exceptions=True)
    judge_duration_ms = round((time.time() - t_judge_start) * 1000)

    judge_results: List[Optional[JudgeResult]] = []
    scores = []
    judge_errors = []
    for out in judge_outcomes:
        if isinstance(out, tuple) and isinstance(out[0], JudgeResult):
            judge_results.append(out[0])
            scores.append(out[0].score)
        else:
            judge_results.append(None)
            scores.append(None)
            judge_errors.append(str(out))

    if all(j is None for j in judge_results) and drafts:
        await emit({
            "step": "judge",
            "role": "judge",
            "model": config.JUDGE_MODEL,
            "status": "error",
            "detail": f"All judge evaluations failed: {'; '.join(judge_errors[:2])}",
        })
    else:
        await emit({
            "step": "judge",
            "role": "judge",
            "model": config.JUDGE_MODEL,
            "status": "done",
            "duration_ms": judge_duration_ms,
            "payload": {"scores": scores},
        })

    # Step 2: Rewrite Phase (Dedicated Rewrite Model)
    await emit({
        "step": "rewrite",
        "role": "rewrite",
        "model": rewrite_model_id,
        "status": "running",
    })
    t_rewrite_start = time.time()
    rewrite_tasks = []
    for d, j in zip(drafts, judge_results):
        if j is not None:
            rewrite_tasks.append(rewrite_one(d, j, tree))
        else:
            async def passthrough(d=d):
                return d, 0
            rewrite_tasks.append(passthrough())

    rewrite_outcomes = await asyncio.gather(*rewrite_tasks, return_exceptions=True)
    rewrite_duration_ms = round((time.time() - t_rewrite_start) * 1000)

    final_drafts: List[Draft] = []
    rewrite_errors = []
    for i, out in enumerate(rewrite_outcomes):
        if isinstance(out, tuple) and isinstance(out[0], Draft):
            final_drafts.append(out[0])
        else:
            # Safe fallback to original draft on rewrite failure
            final_drafts.append(drafts[i])
            rewrite_errors.append(str(out))

    if rewrite_errors and all(isinstance(out, Exception) for out in rewrite_outcomes):
        await emit({
            "step": "rewrite",
            "role": "rewrite",
            "model": rewrite_model_id,
            "status": "error",
            "detail": f"Rewrite calls failed (falling back to original drafts): {rewrite_errors[0]}",
        })
    else:
        await emit({
            "step": "rewrite",
            "role": "rewrite",
            "model": rewrite_model_id,
            "status": "done",
            "duration_ms": rewrite_duration_ms,
            "detail": f"{len(rewrite_errors)} rewrite fallback(s)" if rewrite_errors else None,
        })

    # Compile IssueResult items with full models_used metadata
    models_dict = {
        "drafter": config.DRAFTER_MODEL,
        "judge": config.JUDGE_MODEL,
        "rewrite": rewrite_model_id,
    }
    if code_model_used and config.CODE_MODEL:
        models_dict["code_analysis"] = config.CODE_MODEL

    issue_results: List[IssueResult] = []
    for orig, jg, fin in zip(drafts, judge_results, final_drafts):
        issue_results.append(
            IssueResult(
                id=orig.id,
                original=orig,
                judge=jg,
                final=fin,
                models_used=models_dict,
            )
        )
    return issue_results

async def replay_cached(
    run_id: str,
    cache_data: Dict[str, Any],
    emit: Callable[[Dict[str, Any]], Awaitable[None]]
) -> None:
    """Replays pre-recorded events with realistic delays for zero-cost demo reliability."""
    events = cache_data.get("events", [])
    for ev in events:
        delay = min(max((ev.get("duration_ms") or 500) / 1000.0 * 0.4, 0.2), 1.5)
        await asyncio.sleep(delay)
        await emit(ev)

    if run_id in RUNS:
        RUNS[run_id]["result"] = cache_data.get("result")
        RUNS[run_id]["done"] = True

async def run_pipeline(run_id: str, repo_url: str) -> None:
    """Main pipeline execution coordinating GitHub scan, Scanner, Code Review, Drafter, Judge, and Rewrite."""
    emit = make_emitter(run_id)
    rewrite_model_id = config.REWRITE_MODEL or config.DRAFTER_MODEL
    try:
        owner, repo = parse_repo_url(repo_url)
        cache_file = CACHE_DIR / f"{owner}__{repo}.json"

        # Check demo replay mode
        if config.DEMO_MODE == "cached" and cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            await replay_cached(run_id, cached_data, emit)
            return

        # Emit initial waiting state for all configured roles
        await emit({"step": "github", "role": "github", "model": "GitHub REST API", "status": "waiting"})
        if config.SCANNER_MODEL:
            await emit({"step": "scanner", "role": "scanner", "model": config.SCANNER_MODEL, "status": "waiting"})
        if config.CODE_MODEL:
            await emit({"step": "code_analysis", "role": "code_analysis", "model": config.CODE_MODEL, "status": "waiting"})
        else:
            await emit({
                "step": "code_analysis",
                "role": "code_analysis",
                "model": "Not configured",
                "status": "skipped",
                "detail": "CODE_MODEL is not set in backend .env",
            })
        await emit({"step": "drafter", "role": "drafter", "model": config.DRAFTER_MODEL, "status": "waiting"})
        await emit({"step": "judge", "role": "judge", "model": config.JUDGE_MODEL, "status": "waiting"})
        await emit({"step": "rewrite", "role": "rewrite", "model": rewrite_model_id, "status": "waiting"})

        # Step 1: GitHub Ingestion
        await emit({"step": "github", "role": "github", "model": "GitHub REST API", "status": "running"})
        t_gh_start = time.time()
        summary = await build_repo_summary(repo_url)
        gh_duration_ms = round((time.time() - t_gh_start) * 1000)
        tree_count = len(summary.get("tree", []))
        issues_count = len(summary.get("open_issues", []))
        todos_count = len(summary.get("todos", []))
        detail_msg = f"{tree_count} files, {issues_count} open issues, {todos_count} TODOs"
        await emit({
            "step": "github",
            "role": "github",
            "model": "GitHub REST API",
            "status": "done",
            "duration_ms": gh_duration_ms,
            "detail": detail_msg,
        })

        # Step 2: Scanner (Optional contribution opportunity shortlisting)
        opportunities = None
        if config.SCANNER_MODEL:
            await emit({"step": "scanner", "role": "scanner", "model": config.SCANNER_MODEL, "status": "running"})
            try:
                opportunities, scan_duration_ms = await scan_step(summary)
                await emit({
                    "step": "scanner",
                    "role": "scanner",
                    "model": config.SCANNER_MODEL,
                    "status": "done",
                    "duration_ms": scan_duration_ms,
                    "payload": {"opportunities": opportunities},
                })
            except Exception as scan_err:
                await emit({
                    "step": "scanner",
                    "role": "scanner",
                    "model": config.SCANNER_MODEL,
                    "status": "error",
                    "detail": str(scan_err),
                })

        # Step 3: Code Analysis (Optional Qwen deep source code review)
        code_findings = None
        if config.CODE_MODEL:
            await emit({"step": "code_analysis", "role": "code_analysis", "model": config.CODE_MODEL, "status": "running"})
            try:
                code_findings, code_dur = await code_analysis_step(summary)
                files_analyzed_count = len(summary.get("source_files", {}))
                findings_dicts = [f.model_dump() for f in (code_findings or [])]
                detail_msg = f"{files_analyzed_count} files analyzed, {len(findings_dicts)} findings"
                await emit({
                    "step": "code_analysis",
                    "role": "code_analysis",
                    "model": config.CODE_MODEL,
                    "status": "done",
                    "duration_ms": code_dur,
                    "detail": detail_msg,
                    "payload": {
                        "findings_count": len(findings_dicts),
                        "files_analyzed": files_analyzed_count,
                        "findings": findings_dicts,
                    },
                })
            except Exception as code_err:
                err_str = str(code_err)
                if "404" in err_str:
                    err_msg = f"Model '{config.CODE_MODEL}' not found on {config.LLM_BASE_URL} (404). Clear CODE_MODEL in .env or provide an available model."
                else:
                    err_msg = err_str
                await emit({
                    "step": "code_analysis",
                    "role": "code_analysis",
                    "model": config.CODE_MODEL,
                    "status": "error",
                    "detail": err_msg,
                })
        else:
            await emit({
                "step": "code_analysis",
                "role": "code_analysis",
                "model": "Not configured",
                "status": "skipped",
                "detail": "CODE_MODEL is not set in backend .env",
            })

        # Step 4: Drafter (Nemotron Ultra)
        await emit({"step": "drafter", "role": "drafter", "model": config.DRAFTER_MODEL, "status": "running"})
        try:
            drafts, draft_duration_ms = await draft_step(summary, opportunities, code_findings)
            await emit({
                "step": "drafter",
                "role": "drafter",
                "model": config.DRAFTER_MODEL,
                "status": "done",
                "duration_ms": draft_duration_ms,
                "payload": {"count": len(drafts)},
            })
        except Exception as draft_err:
            await emit({
                "step": "drafter",
                "role": "drafter",
                "model": config.DRAFTER_MODEL,
                "status": "error",
                "detail": str(draft_err),
            })
            raise draft_err

        # Step 5: Judge & Rewrite (Nemotron Nano & Gemma)
        issues = await process_drafts(drafts, summary, emit, code_model_used=bool(config.CODE_MODEL))

        run_result = RunResult(
            repo=f"{owner}/{repo}",
            issues=issues,
            code_findings=code_findings or [],
        )
        result_dict = run_result.model_dump()
        RUNS[run_id]["result"] = result_dict

        # Save to cache
        cache_payload = {
            "events": RUNS[run_id]["events"],
            "result": result_dict,
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_payload, f, indent=2)

        # Emit completion
        await emit({
            "step": "final",
            "role": "system",
            "model": "Kindling",
            "status": "done",
            "payload": result_dict,
        })
        RUNS[run_id]["done"] = True

    except Exception as exc:
        await emit({
            "step": "final",
            "role": "system",
            "model": "Kindling",
            "status": "error",
            "detail": str(exc),
        })
        RUNS[run_id]["done"] = True
