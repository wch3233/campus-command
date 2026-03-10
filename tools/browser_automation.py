"""
browser_automation.py — Web page fetching and content extraction.

Uses urllib for simple HTTP fetches. Strips HTML tags for clean text.
Optionally supports Playwright if installed (for JS-rendered pages).
"""

import urllib.request
import urllib.error
import re
import html
from typing import Optional


def fetch_page(url: str, timeout: int = 15) -> Optional[str]:
    """
    Fetch a web page and return its text content (HTML stripped).

    Args:
        url:     Full URL to fetch.
        timeout: Request timeout in seconds.

    Returns:
        Plain text content, or None on failure.
    """
    try:
        req = urllib.request.Request(url)
        req.add_header(
            "User-Agent",
            "Mozilla/5.0 (compatible; CampusCommand/1.0; educational-bot)"
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        return _strip_html(raw)
    except urllib.error.HTTPError as e:
        print(f"[browser] HTTP {e.code} fetching {url}")
        return None
    except Exception as e:
        print(f"[browser] Error fetching {url}: {e}")
        return None


def fetch_page_playwright(url: str) -> Optional[str]:
    """
    Fetch a JavaScript-rendered page using Playwright.

    Only works if playwright is installed: pip install playwright && playwright install chromium

    Args:
        url: Full URL to fetch.

    Returns:
        Plain text content, or None if Playwright is not available.
    """
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=20000)
            page.wait_for_load_state("networkidle", timeout=10000)
            content = page.content()
            browser.close()
            return _strip_html(content)
    except ImportError:
        print("[browser] Playwright not installed. Falling back to urllib.")
        return fetch_page(url)
    except Exception as e:
        print(f"[browser] Playwright error: {e}")
        return fetch_page(url)


def _strip_html(raw: str) -> str:
    """Remove HTML tags, decode entities, collapse whitespace."""
    # Remove scripts and styles
    raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw, flags=re.DOTALL | re.IGNORECASE)
    # Remove all tags
    raw = re.sub(r"<[^>]+>", " ", raw)
    # Decode HTML entities
    raw = html.unescape(raw)
    # Collapse whitespace
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw[:8000]  # Cap at 8K chars to keep prompts manageable


def extract_summary(text: str, max_chars: int = 2000) -> str:
    """
    Return a truncated version of page text suitable for injecting into a prompt.

    Args:
        text:      Plain text page content.
        max_chars: Maximum characters to return.

    Returns:
        Truncated text.
    """
    if not text:
        return "No content available."
    return text[:max_chars] + ("..." if len(text) > max_chars else "")
