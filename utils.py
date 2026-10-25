import hashlib
import re
from typing import Any, Dict, List, Optional


def extract_llm_content(response: Any) -> str:
    """Safely extract string content from any LLM response object.

    Handles LangChain BaseMessage (AIMessage), strings, dicts, or other
    objects.
    """
    if response is None:
        return ""
    if isinstance(response, str):
        return response
    if hasattr(response, "content"):
        content = response.content
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            # E.g. Claude / modern LangChain multi-part response
            parts = []
            for part in content:
                if isinstance(part, str):
                    parts.append(part)
                elif isinstance(part, dict) and "text" in part:
                    parts.append(part["text"])
            return "".join(parts)
        return str(content)
    if isinstance(response, dict):
        return str(response.get("content", response.get("text", str(response))))
    return str(response)


def clean_text(text: Optional[str], preserve_newlines: bool = False) -> str:
    """Clean unnecessary whitespace from text.

    Args:
        text: The input text.
        preserve_newlines: If True, collapse multiple blank lines into max 2
          newlines, preserving paragraph structure. If False, collapse all
          whitespace to single space.
    """
    if text is None:
        return ""

    text = str(text)

    if preserve_newlines:
        # Normalize spaces/tabs
        text = re.sub(r"[ \t]+", " ", text)
        # Limit consecutive newlines to max 2
        text = re.sub(r"\n\s*\n+", "\n\n", text)
    else:
        # Remove all excessive whitespace
        text = re.sub(r"\s+", " ", text)

    return text.strip()


def truncate_text(text: Optional[str], max_length: int = 5000) -> str:
    """Limit text length before sending it to the LLM to prevent context

    overflow.
    """
    if not text:
        return ""

    text = str(text)

    if len(text) <= max_length:
        return text

    return text[:max_length] + "\n...[truncated]"


def format_documents(documents: List[Dict[str, Any]], max_chars_per_doc: int = 2500) -> str:
    """Convert retrieved documents into a clean, formatted text block.

    Args:
        documents: List of document dicts.
        max_chars_per_doc: Maximum character limit for each document's content.
    """
    formatted = []

    for i, doc in enumerate(documents, start=1):
        content = truncate_text(doc.get("content", ""), max_chars_per_doc)
        source = doc.get("source", "Unknown")
        title = doc.get("title", "Unknown")
        url = doc.get("url", "")
        url_line = f"URL: {url}\n" if url else ""

        formatted.append(
            f"--- Document {i} ---\n"
            f"Title: {title}\n"
            f"Source: {source}\n"
            f"{url_line}"
            f"Content:\n{content}"
        )

    return "\n\n".join(formatted)


def remove_duplicates(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate retrieved documents using content & title hashing.

    Optimized for memory by storing hashes rather than entire document texts.
    """
    unique = []
    seen = set()

    for result in results:
        content = result.get("content", "")
        title = result.get("title", "")
        url = result.get("url", "")

        # Key on URL if available, otherwise hash normalized content and title
        if url and url.strip():
            key = f"url:{url.strip().lower()}"
        else:
            text_rep = f"{title.strip().lower()}:{content.strip()[:500]}"
            key = hashlib.md5(text_rep.encode("utf-8", errors="ignore")).hexdigest()

        if key and key not in seen:
            seen.add(key)
            unique.append(result)

    return unique


def get_source(result: Dict[str, Any]) -> str:
    """Safely obtain the source of a retrieved document."""
    return result.get("source", "Unknown")


def get_content(result: Dict[str, Any]) -> str:
    """Safely obtain document content."""
    return result.get("content", "")
