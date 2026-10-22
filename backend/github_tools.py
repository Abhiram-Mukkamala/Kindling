import asyncio
import base64
import re
from typing import Tuple, List, Dict, Any, Optional
import httpx
from backend import config

def _get_headers() -> Dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Kindling-Agent/1.0",
    }
    token = config.GITHUB_TOKEN.strip() if config.GITHUB_TOKEN else ""
    if token and not token.startswith("ghp_your_") and not token.startswith("your_"):
        headers["Authorization"] = f"Bearer {token}"
    return headers

def parse_repo_url(url: str) -> Tuple[str, str]:
    """
    Parses GitHub URL or 'owner/repo' shorthand into (owner, repo).
    Examples:
      - https://github.com/facebook/react
      - https://github.com/facebook/react.git
      - facebook/react
    """
    url = url.strip()
    # Remove trailing slashes and .git
    url = re.sub(r"\.git/?$", "", url)
    url = url.rstrip("/")

    if "github.com/" in url:
        part = url.split("github.com/")[-1]
    else:
        part = url

    tokens = [t for t in part.split("/") if t]
    if len(tokens) >= 2:
        return tokens[0], tokens[1]
    raise ValueError(f"Could not parse valid GitHub repository from '{url}'. Format: 'owner/repo' or 'https://github.com/owner/repo'")

async def get_repo_meta(client: httpx.AsyncClient, owner: str, repo: str) -> Dict[str, Any]:
    """Fetches repository metadata: name, description, default_branch."""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    resp = await client.get(url, headers=_get_headers(), timeout=15.0)
    resp.raise_for_status()
    data = resp.json()
    return {
        "name": data.get("name", repo),
        "owner": owner,
        "description": data.get("description") or "No description provided.",
        "default_branch": data.get("default_branch", "main"),
    }

async def get_tree(client: httpx.AsyncClient, owner: str, repo: str, branch: str) -> List[str]:
    """
    Fetches git tree recursively, filtered and capped at 200 files.
    Prefers shorter paths first.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    resp = await client.get(url, headers=_get_headers(), timeout=20.0)
    if resp.status_code != 200:
        return []

    data = resp.json()
    raw_tree = data.get("tree", [])

    ignored_substrs = (
        "node_modules", "dist/", "build/", ".git/", "vendor/", "__pycache__", ".venv"
    )
    ignored_exts = (
        ".lock", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf", ".zip", ".min.js", ".map"
    )

    filtered = []
    for item in raw_tree:
        if item.get("type") == "blob":
            path = item.get("path", "")
            if any(sub in path for sub in ignored_substrs):
                continue
            if any(path.endswith(ext) for ext in ignored_exts):
                continue
            filtered.append(path)

    # Prefer shorter paths first and cap at 200
    filtered.sort(key=len)
    return filtered[:200]

async def get_readme(client: httpx.AsyncClient, owner: str, repo: str) -> str:
    """Fetches repository README, returning first 6000 decoded characters."""
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    resp = await client.get(url, headers=_get_headers(), timeout=15.0)
    if resp.status_code != 200:
        return ""
    data = resp.json()
    content_b64 = data.get("content", "")
    try:
        decoded = base64.b64decode(content_b64).decode("utf-8", errors="replace")
        return decoded[:6000]
    except Exception:
        return ""

async def get_open_issues(client: httpx.AsyncClient, owner: str, repo: str) -> List[Dict[str, Any]]:
    """Fetches up to 15 open issues (excluding pull requests)."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues?state=open&per_page=30"
    resp = await client.get(url, headers=_get_headers(), timeout=15.0)
    if resp.status_code != 200:
        return []

    items = resp.json()
    issues = []
    for it in items:
        if "pull_request" in it:
            continue
        body = (it.get("body") or "")[:500]
        labels = [lbl["name"] if isinstance(lbl, dict) else str(lbl) for lbl in it.get("labels", [])]
        issues.append({
            "number": it.get("number"),
            "title": it.get("title", ""),
            "body": body,
            "labels": labels,
        })
        if len(issues) >= 15:
            break
    return issues

async def get_file(client: httpx.AsyncClient, owner: str, repo: str, path: str, branch: str) -> str:
    """Fetches a single file content up to 20000 bytes."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    try:
        resp = await client.get(url, headers=_get_headers(), timeout=10.0)
        if resp.status_code != 200:
            return ""
        data = resp.json()
        if data.get("size", 0) > 20000:
            return ""
        content_b64 = data.get("content", "")
        return base64.b64decode(content_b64).decode("utf-8", errors="replace")
    except Exception:
        return ""

async def find_todos(client: httpx.AsyncClient, owner: str, repo: str, branch: str, paths: List[str]) -> List[Dict[str, Any]]:
    """Scans up to 15 code files for TODO/FIXME comments, capped at 20 findings."""
    code_exts = (".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".c", ".cpp", ".rb", ".php")
    candidate_paths = [p for p in paths if any(p.endswith(ext) for ext in code_exts)][:15]

    sem = asyncio.Semaphore(5)
    todos: List[Dict[str, Any]] = []

    async def inspect(p: str):
        async with sem:
            content = await get_file(client, owner, repo, p, branch)
            if not content:
                return
            for idx, line in enumerate(content.splitlines(), start=1):
                if "TODO" in line or "FIXME" in line:
                    clean_line = line.strip()[:200]
                    todos.append({"path": p, "line": idx, "text": clean_line})
                    if len(todos) >= 20:
                        return

    tasks = [inspect(p) for p in candidate_paths]
    await asyncio.gather(*tasks)
    return todos[:20]

async def build_repo_summary(repo_url: str) -> Dict[str, Any]:
    """Compiles complete repository summary dict for model prompting."""
    owner, repo = parse_repo_url(repo_url)
    async with httpx.AsyncClient() as client:
        meta = await get_repo_meta(client, owner, repo)
        branch = meta["default_branch"]

        tree_task = get_tree(client, owner, repo, branch)
        readme_task = get_readme(client, owner, repo)
        issues_task = get_open_issues(client, owner, repo)

        tree, readme, issues = await asyncio.gather(tree_task, readme_task, issues_task)
        todos = await find_todos(client, owner, repo, branch, tree)

        return {
            "owner": owner,
            "repo": repo,
            "description": meta["description"],
            "default_branch": branch,
            "tree": tree,
            "readme": readme,
            "open_issues": issues,
            "todos": todos,
        }

async def create_issue(target_repo: str, title: str, body: str, labels: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Creates an issue on the target repo via GitHub REST API.
    Retries once without labels if GitHub returns 422.
    """
    if not config.GITHUB_TOKEN or not config.GITHUB_TOKEN.strip():
        raise ValueError("Cannot create GitHub issue: GITHUB_TOKEN is not configured in .env")

    owner, repo = parse_repo_url(target_repo)
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    headers = _get_headers()

    payload: Dict[str, Any] = {
        "title": title,
        "body": body,
    }
    if labels:
        payload["labels"] = labels

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=payload, timeout=20.0)
        # If labels don't exist on target repo, GitHub returns 422 Unprocessable Entity
        if resp.status_code == 422 and labels:
            del payload["labels"]
            resp = await client.post(url, headers=headers, json=payload, timeout=20.0)

        if resp.status_code not in (200, 201):
            raise ValueError(f"GitHub API error ({resp.status_code}): {resp.text}")

        data = resp.json()
        return {"html_url": data.get("html_url", "")}
