import re
import os
import base64
from typing import Dict, List, Any, Optional, Tuple
import httpx
from backend import config

GITHUB_API_BASE = "https://api.github.com"

def parse_repo_url(repo_url: str) -> Tuple[str, str]:
    """Extract (owner, repo) from a GitHub URL or 'owner/repo' string."""
    cleaned = repo_url.strip().rstrip("/")
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]
    
    # Handle full URL e.g. https://github.com/owner/repo
    match = re.search(r"github\.com[/:]([^/]+)/([^/]+)", cleaned)
    if match:
        return match.group(1), match.group(2)
    
    # Handle shorthand owner/repo
    parts = cleaned.split("/")
    if len(parts) == 2 and not parts[0].startswith("http"):
        return parts[0], parts[1]
        
    raise ValueError(f"Could not parse valid GitHub repository from: '{repo_url}'. Expected 'owner/repo' or 'https://github.com/owner/repo'.")

def get_headers() -> Dict[str, str]:
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Kindling-App/1.0",
    }
    token = config.GITHUB_TOKEN.strip()
    if token and not token.startswith("ghp_your"):
        headers["Authorization"] = f"Bearer {token}"
    return headers

async def fetch_repo_tree(client: httpx.AsyncClient, owner: str, repo: str) -> List[str]:
    """Fetch repo tree capped at 200 relevant files."""
    # First get repo default branch
    repo_resp = await client.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}", headers=get_headers())
    if repo_resp.status_code != 200:
        raise ValueError(f"Failed to access GitHub repo {owner}/{repo}: {repo_resp.status_code} {repo_resp.text}")
    
    default_branch = repo_resp.json().get("default_branch", "main")
    
    # Fetch recursive tree
    tree_resp = await client.get(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1",
        headers=get_headers(),
    )
    if tree_resp.status_code != 200:
        return []
    
    tree_data = tree_resp.json().get("tree", [])
    
    ignored_patterns = [
        "node_modules/", ".git/", ".venv/", "dist/", "build/", "__pycache__/",
        ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".lock", "-lock.json",
        ".min.js", ".min.css", ".woff", ".woff2", ".ttf", ".pdf"
    ]
    
    filtered_paths = []
    for item in tree_data:
        if item.get("type") == "blob":
            path = item.get("path", "")
            if not any(ign in path for ign in ignored_patterns):
                filtered_paths.append(path)
            if len(filtered_paths) >= 200:
                break
                
    return filtered_paths

async def fetch_readme(client: httpx.AsyncClient, owner: str, repo: str) -> str:
    """Fetch repository README content, capped at 3000 chars."""
    headers = get_headers()
    headers["Accept"] = "application/vnd.github.raw+json"
    resp = await client.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}/readme", headers=headers)
    if resp.status_code == 200:
        text = resp.text.strip()
        return text[:3000] + ("\n...[truncated]" if len(text) > 3000 else "")
    return "No README found."

async def fetch_open_issues(client: httpx.AsyncClient, owner: str, repo: str, limit: int = 5) -> List[Dict[str, str]]:
    """Fetch up to `limit` open issues (excluding pull requests)."""
    resp = await client.get(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues",
        headers=get_headers(),
        params={"state": "open", "per_page": limit * 2},
    )
    if resp.status_code != 200:
        return []
        
    items = resp.json()
    issues = []
    for it in items:
        # Ignore pull requests
        if "pull_request" in it:
            continue
        title = it.get("title", "")
        body = (it.get("body") or "")[:400]
        issues.append({"title": title, "body": body})
        if len(issues) >= limit:
            break
            
    return issues

def is_comment_todo(line: str) -> Optional[Tuple[str, str]]:
    """
    Checks if a line contains a real TODO/FIXME/HACK/BUG comment.
    Rules:
    - Line (stripped) starts with '#', '//', '/*', '*' OR contains ' # ' or ' // ' before keyword.
    - Skip lines where the keyword sits inside a string literal or regex.
    """
    stripped = line.strip()
    if not stripped:
        return None

    # Search for keyword
    match = re.search(r"\b(TODO|FIXME|HACK|BUG)\b", line, re.IGNORECASE)
    if not match:
        return None

    kw_start, kw_end = match.start(), match.end()
    tag = match.group(1).upper()
    before_kw = line[:kw_start]
    after_kw = line[kw_end:]

    # Skip lines where keyword sits inside string literal or regex
    # Count unescaped quotes before keyword
    single_q = len(re.findall(r"(?<!\\)'", before_kw))
    double_q = len(re.findall(r'(?<!\\)"', before_kw))
    backticks = len(re.findall(r'(?<!\\)`', before_kw))
    if (single_q % 2 != 0) or (double_q % 2 != 0) or (backticks % 2 != 0):
        return None

    # Check regex literal or quoted string immediately around keyword
    if (before_kw.rstrip().endswith("/") and after_kw.lstrip().startswith("/")) or \
       (before_kw.rstrip().endswith("r'") or before_kw.rstrip().endswith('r"')):
        return None

    # Comment prefix check:
    starts_with_comment = (
        stripped.startswith("#") or
        stripped.startswith("//") or
        stripped.startswith("/*") or
        stripped.startswith("*")
    )
    has_inline_comment = (" # " in before_kw) or (" // " in before_kw)

    if not (starts_with_comment or has_inline_comment):
        return None

    return tag, stripped

async def find_todos(client: httpx.AsyncClient, owner: str, repo: str, tree: List[str], max_files: int = 5) -> List[Dict[str, Any]]:
    """
    Scan up to max_files source files for real TODO / FIXME / HACK / BUG comments.
    Includes the 5 lines of code before and after each match as a 'snippet' field.
    """
    todo_matches = []
    scannable_extensions = (".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java")
    
    target_files = [f for f in tree if f.endswith(scannable_extensions)][:max_files]
    headers = get_headers()
    headers["Accept"] = "application/vnd.github.raw+json"
    
    for file_path in target_files:
        try:
            resp = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{file_path}",
                headers=headers,
            )
            if resp.status_code == 200:
                lines = resp.text.splitlines()
                for idx, line in enumerate(lines[:300]):
                    res = is_comment_todo(line)
                    if res:
                        tag, content = res
                        start_idx = max(0, idx - 5)
                        end_idx = min(len(lines), idx + 6)
                        snippet = "\n".join(lines[start_idx:end_idx])

                        todo_matches.append({
                            "file": file_path,
                            "line": idx + 1,
                            "tag": tag,
                            "content": content,
                            "snippet": snippet,
                        })
                        if len(todo_matches) >= 6:
                            return todo_matches
        except Exception:
            continue
            
    return todo_matches

grep_todos = find_todos

async def get_repo_summary(repo_url: str) -> Dict[str, Any]:
    """Aggregate tree, README, open issues, and TODOs into a single context object."""
    owner, repo = parse_repo_url(repo_url)
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        tree = await fetch_repo_tree(client, owner, repo)
        readme = await fetch_readme(client, owner, repo)
        open_issues = await fetch_open_issues(client, owner, repo, limit=5)
        todos = await grep_todos(client, owner, repo, tree, max_files=5)
        
    return {
        "owner": owner,
        "repo": repo,
        "tree": tree[:100],  # keep top 100 for context prompt
        "total_files": len(tree),
        "readme": readme,
        "open_issues": open_issues,
        "todos": todos,
    }

async def create_issue(target_repo: str, title: str, body: str, labels: Optional[List[str]] = None) -> Dict[str, Any]:
    """Create a new issue on target_repo using GITHUB_TOKEN and return dict with html_url."""
    target = target_repo.strip() if target_repo else config.TARGET_REPO.strip()
    if not target or target in ("your-org-or-username/demo-repo", "owner/demo-repo"):
        raise ValueError("TARGET_REPO is not configured in .env.")
        
    owner, repo = parse_repo_url(target)
    headers = get_headers()
    if "Authorization" not in headers:
        raise ValueError("GITHUB_TOKEN is required to post issues.")
        
    payload: Dict[str, Any] = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues",
            headers=headers,
            json=payload,
        )
        if resp.status_code == 422 and labels:
            del payload["labels"]
            resp = await client.post(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues",
                headers=headers,
                json=payload,
            )
        if resp.status_code in (200, 201):
            return {"html_url": resp.json().get("html_url", "")}
        else:
            raise ValueError(f"GitHub API error ({resp.status_code}): {resp.text}")

async def create_issue_on_target_repo(title: str, body: str) -> str:
    res = await create_issue(config.TARGET_REPO, title, body)
    return res.get("html_url", "")

async def build_repo_summary(repo_url: str) -> Dict[str, Any]:
    summary = await get_repo_summary(repo_url)
    return {
        "owner": summary.get("owner", ""),
        "repo": summary.get("repo", ""),
        "description": f"Repository {summary.get('owner')}/{summary.get('repo')}",
        "default_branch": "main",
        "tree": summary.get("tree", []),
        "readme": summary.get("readme", ""),
        "open_issues": summary.get("open_issues", []),
        "todos": summary.get("todos", []),
    }
