"""
github_api.py — GitHub API integration.

Allows agents to search GitHub for code examples, read READMEs,
and look up repositories relevant to student projects.
"""

import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GITHUB_TOKEN


def search_repositories(query: str, limit: int = 5) -> list[dict]:
    """
    Search GitHub repositories matching a query.

    Args:
        query: Search string (e.g., "python calculator beginner").
        limit: Max number of repos to return.

    Returns:
        List of dicts: [{"name", "description", "url", "stars", "language"}, ...]
    """
    token = GITHUB_TOKEN or os.environ.get("GITHUB_TOKEN", "")
    encoded = urllib.parse.quote(query)
    url = f"https://api.github.com/search/repositories?q={encoded}&sort=stars&per_page={limit}"

    try:
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        if token:
            req.add_header("Authorization", f"Bearer {token}")

        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        results = []
        for item in data.get("items", [])[:limit]:
            results.append({
                "name": item.get("full_name", ""),
                "description": item.get("description", ""),
                "url": item.get("html_url", ""),
                "stars": item.get("stargazers_count", 0),
                "language": item.get("language", ""),
            })
        return results
    except Exception as e:
        print(f"[github_api] Error: {e}")
        return []


def get_readme(owner: str, repo: str) -> Optional[str]:
    """
    Fetch the README for a GitHub repository.

    Args:
        owner: Repository owner (username or org).
        repo:  Repository name.

    Returns:
        README text, or None on failure.
    """
    token = GITHUB_TOKEN or os.environ.get("GITHUB_TOKEN", "")
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"

    try:
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/vnd.github.raw+json")
        if token:
            req.add_header("Authorization", f"Bearer {token}")

        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"[github_api] README error: {e}")
        return None


def format_repo_results(results: list[dict]) -> str:
    """Format repository results as readable text."""
    if not results:
        return "No GitHub repositories found."
    lines = []
    for r in results:
        lines.append(f"📦 {r['name']} ({r['language'] or 'unknown'}) ★{r['stars']}")
        if r["description"]:
            lines.append(f"   {r['description']}")
        lines.append(f"   {r['url']}")
        lines.append("")
    return "\n".join(lines)
