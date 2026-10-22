import asyncio
import sys
import json
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from backend import config, github_tools, pipeline
from backend.schemas import Draft

async def cli_emit(event: dict):
    step = event.get("step", "").upper()
    role = event.get("role", "")
    status = event.get("status", "")
    dur = f" ({event.get('duration_ms')}ms)" if event.get("duration_ms") else ""
    detail = f" - {event.get('detail')}" if event.get("detail") else ""
    print(f"[{status.upper():7s}] {step:8s} | Role: {role:8s}{dur}{detail}")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_cli.py <repo_url_or_owner/repo>")
        sys.exit(1)

    repo_url = sys.argv[1]
    print("=" * 65)
    print(f"KINDLING CLI - Open-Model Contributor Issue Drafter")
    print(f"Target Repo: {repo_url}")
    print(f"Drafter: {config.DRAFTER_MODEL or '(not set)'}")
    print(f"Judge:   {config.JUDGE_MODEL or '(not set)'}")
    print(f"Rewrite: {config.REWRITE_MODEL or config.DRAFTER_MODEL or '(not set)'}")
    if config.CODE_MODEL:
        print(f"Code:    {config.CODE_MODEL}")
    print("=" * 65)

    if config.JUDGE_MODEL and config.DRAFTER_MODEL and config.JUDGE_MODEL == config.DRAFTER_MODEL:
        print("\n[WARNING] JUDGE_MODEL and DRAFTER_MODEL are identical! A separate model family is strongly recommended for independent review.\n")

    print("\n1. Fetching repository metadata & tree from GitHub...")
    t0 = time.time()
    try:
        summary = await github_tools.build_repo_summary(repo_url)
    except Exception as e:
        print(f"[ERROR] Failed to fetch repo summary: {e}")
        sys.exit(1)

    tree = summary.get("tree", [])
    print(f"   [DONE] in {time.time()-t0:.2f}s: {len(tree)} files, {len(summary['open_issues'])} open issues, {len(summary['todos'])} TODO comments.")

    print("\n2. Drafter generating newcomer-ready issue drafts...")
    try:
        drafts, draft_dur = await pipeline.draft_step(summary)
        print(f"   [DONE] in {draft_dur}ms. Generated {len(drafts)} draft(s).")
    except Exception as e:
        print(f"[ERROR] Drafter model call failed: {e}")
        sys.exit(1)

    # Validate file paths against repository tree (files_to_touch only)
    print("\n   Checking file path references against repository tree:")
    for d in drafts:
        for f in d.files_to_touch:
            if f not in tree:
                print(f"   [PATH WARNING] '{f}' from draft '{d.title}' was not found in repo tree!")
            else:
                print(f"   [PATH OK] '{f}'")
        for nf in getattr(d, 'new_files', []):
            print(f"   [NEW FILE] '{nf}' (creation proposed, no warning)")

    print("\n3. Running Judge evaluation and Drafter rewrite in parallel...")
    try:
        issues = await pipeline.process_drafts(drafts, summary, cli_emit)
    except Exception as e:
        print(f"[ERROR] Judge/Rewrite processing failed: {e}")
        sys.exit(1)

    print("\n" + "=" * 65)
    print("PIPELINE RESULTS:")
    print("=" * 65)
    for idx, iss in enumerate(issues, start=1):
        orig = iss.original
        jg = iss.judge
        fin = iss.final or orig

        print(f"\n--- ISSUE #{idx} (Difficulty: {fin.difficulty.upper()} | Source: {fin.source}) ---")
        print(f"ORIGINAL TITLE : {orig.title}")
        print(f"ORIGINAL CONTEXT: {orig.context}")
        print(f"FILES TO TOUCH  : {', '.join(orig.files_to_touch) or '(none)'}")
        if getattr(orig, 'new_files', None):
            print(f"NEW FILES       : {', '.join(orig.new_files)}")

        if jg:
            print(f"\nJUDGE REVIEW    : Score {jg.score}/10")
            print(f"CRITIQUE        : {jg.critique}")
            if jg.problems:
                print(f"PROBLEMS NOTED  : {', '.join(jg.problems)}")
        else:
            print("\nJUDGE REVIEW    : (Judge evaluation skipped or unavailable)")

        print(f"\nFINAL REWRITTEN TITLE: {fin.title}")
        print(f"FINAL CONTEXT       : {fin.context}")
        print(f"ACCEPTANCE CRITERIA :")
        for ac in fin.acceptance_criteria:
            print(f"  [ ] {ac}")
        if iss.models_used:
            models_str = ", ".join(f"{k.capitalize()}: {v.split('/').pop()}" for k, v in iss.models_used.items())
            print(f"MODELS USED         : {models_str}")

    print("\n" + "=" * 65)
    print("Done! All drafts verified and ready.")

if __name__ == "__main__":
    asyncio.run(main())
