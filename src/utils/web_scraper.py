"""Utilities for scraping web pages into clean markdown-like text."""

from __future__ import annotations

import re
import importlib
from typing import List

import requests


def scrape_url_to_markdown(url: str) -> str:
    """
    Fetch a URL and convert meaningful page text to clean markdown-ish format.

    The output keeps a simple paragraph/list structure so it can be used as LLM context.
    On failure, it returns a standardized system error string.
    """
    try:
        BeautifulSoup = importlib.import_module("bs4").BeautifulSoup
    except Exception as exc:
        return f"[System Error: Missing dependency for web scraping (beautifulsoup4): {str(exc)}]"

    try:
        response = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                )
            },
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return f"[System Error: Failed to fetch URL '{url}': {str(exc)}]"

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = _normalize_whitespace(soup.title.string)

    blocks: List[str] = []

    for element in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote"]):
        text = _normalize_whitespace(element.get_text(" ", strip=True))
        if not text:
            continue

        if element.name and element.name.startswith("h"):
            blocks.append(f"## {text}")
        elif element.name == "li":
            blocks.append(f"- {text}")
        elif element.name == "blockquote":
            blocks.append(f"> {text}")
        else:
            blocks.append(text)

    if not blocks:
        fallback_text = _normalize_whitespace(soup.get_text(" ", strip=True))
        if not fallback_text:
            return f"[System Error: URL '{url}' returned no meaningful text content.]"
        blocks = [fallback_text]

    lines: List[str] = [f"# Web Source", f"URL: {url}"]
    if title:
        lines.append(f"Title: {title}")
    lines.append("")
    lines.extend(blocks)

    return "\n\n".join(lines).strip()


def _normalize_whitespace(text: str) -> str:
    """Collapse noisy whitespace while preserving readable sentence spacing."""
    return re.sub(r"\s+", " ", text).strip()
