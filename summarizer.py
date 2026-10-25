# summarizer.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List
from utils import extract_llm_content, truncate_text


class PaperSummarizer:
    """Summarizes research papers concurrently and extracts structured scientific insights."""

    def __init__(self, llm: Any, max_workers: int = 4):
        self.llm = llm
        self.max_workers = max_workers

    def _summarize_single(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize a single paper."""
        content = paper.get("content", "")
        title = paper.get("title", "Unknown")
        source = paper.get("source", "unknown")
        url = paper.get("url", "")

        if not content or not str(content).strip():
            return {
                "title": title,
                "source": source,
                "url": url,
                "summary": "No content available to summarize."
            }

        # Truncate content to avoid exceeding context window
        safe_content = truncate_text(content, max_length=4000)

        prompt = f"""You are an expert scientific research assistant.

Summarize the following research paper objectively and concisely.

Title: {title}
Source: {source}

Paper Content:
{safe_content}

Extract the following structured insights:
1. Core Research Problem & Motivation
2. Proposed Method / Technical Approach
3. Main Quantitative or Qualitative Results
4. Key Novelty / Contributions
5. Limitations & Edge Cases Mentioned
6. Proposed Future Work

Use only the information provided. If an aspect is not mentioned, write "Not specified".
"""
        try:
            response = self.llm.invoke(prompt)
            summary_text = extract_llm_content(response)
        except Exception as e:
            summary_text = f"Summarization failed for this paper: {str(e)}"

        return {
            "title": title,
            "source": source,
            "url": url,
            "summary": summary_text
        }

    def summarize(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Summarize a list of papers in parallel for optimal speed."""
        if not papers:
            return []

        # Filter papers with non-empty content
        valid_papers = [p for p in papers if p.get("content", "").strip()]
        if not valid_papers:
            return []

        # If only 1 paper, run directly without thread pool overhead
        if len(valid_papers) == 1:
            return [self._summarize_single(valid_papers[0])]

        # Concurrently summarize papers to significantly reduce latency
        results = [None] * len(valid_papers)
        workers = min(len(valid_papers), self.max_workers)

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_idx = {
                executor.submit(self._summarize_single, paper): idx
                for idx, paper in enumerate(valid_papers)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    paper = valid_papers[idx]
                    results[idx] = {
                        "title": paper.get("title", "Unknown"),
                        "source": paper.get("source", "unknown"),
                        "url": paper.get("url", ""),
                        "summary": f"Failed to process summary: {str(e)}"
                    }

        return [r for r in results if r is not None]
