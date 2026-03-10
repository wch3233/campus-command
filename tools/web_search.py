"""
web_search.py — Web search tool.

Supports Brave Search API (preferred) with DuckDuckGo as a fallback.
Returns a list of result dicts with title, url, and snippet.
"""

import os
import sys
import json
import urllib.parse
import urllib.request
import urllib.error
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BRAVE_API_KEY


def search(query: str, count: int = 5) -> list[dict]:
    """
    Search the web for the given query.

    Tries Brave Search API first; falls back to DuckDuckGo Instant Answer API.

    Args:
        query: Search query string.
        count: Max number of results to return.

    Returns:
        List of dicts: [{"title": str, "url": str, "snippet": str}, ...]
        Returns empty list on total failure.
    """
    key = BRAVE_API_KEY or os.environ.get("BRAVE_API_KEY", "")

    if key:
        results = _brave_search(query, count, key)
        if results:
            return results

    # Fallback: DuckDuckGo Instant Answer API
    return _duckduckgo_search(query, count)


def _brave_search(query: str, count: int, api_key: str) -> list[dict]:
    """Search using the Brave Search API."""
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://api.search.brave.com/res/v1/web/search?q={encoded}&count={count}"
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/json")
        req.add_header("Accept-Encoding", "gzip")
        req.add_header("X-Subscription-Token", api_key)

        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        results = []
        for item in data.get("web", {}).get("results", [])[:count]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("description", ""),
            })
        return results
    except Exception as e:
        print(f"[web_search] Brave API error: {e}")
        return []


def _duckduckgo_search(query: str, count: int) -> list[dict]:
    """Fallback search using DuckDuckGo Instant Answer API."""
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "CampusCommand/1.0 (educational tool)")

        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        results = []

        # Abstract result
        if data.get("AbstractText"):
            results.append({
                "title": data.get("Heading", "Summary"),
                "url": data.get("AbstractURL", ""),
                "snippet": data["AbstractText"],
            })

        # Related topics
        for topic in data.get("RelatedTopics", [])[:count - len(results)]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "title": topic.get("Text", "")[:80],
                    "url": topic.get("FirstURL", ""),
                    "snippet": topic.get("Text", ""),
                })

        return results[:count]
    except Exception as e:
        print(f"[web_search] DuckDuckGo error: {e}")
        return []


def format_results(results: list[dict]) -> str:
    """Format search results as a readable string for injection into prompts."""
    if not results:
        return "No search results found."
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}")
        lines.append(f"   URL: {r['url']}")
        lines.append(f"   {r['snippet']}")
        lines.append("")
    return "\n".join(lines)
