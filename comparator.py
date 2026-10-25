# comparator.py
from typing import Any, Dict, List
from utils import extract_llm_content, truncate_text


class PaperComparator:
    """Compares and synthesizes multiple research papers or literature

    summaries.
    """

    def __init__(self, llm: Any):
        self.llm = llm

    def compare(self, summaries: List[Dict[str, Any]]) -> str:
        """Compare research papers or synthesize a single paper."""
        if not summaries:
            return "No literature summaries available to compare."

        # If only one paper is available, synthesize its core contributions instead of failing
        if len(summaries) == 1:
            paper = summaries[0]
            title = paper.get("title", "Unknown")
            source = paper.get("source", "Unknown")
            summary = paper.get("summary", "")

            single_prompt = f"""You are an expert scientific literature analyst.

Analyze and synthesize the following research paper:

Title: {title}
Source: {source}
Summary & Details:
{summary}

Provide a structured critical synthesis:
1. Core Research Problem & Motivation
2. Key Methodology & Innovations
3. Major Empirical or Theoretical Findings
4. Acknowledged Limitations & Boundaries
5. Open Questions for Future Work

Be rigorous and objective.
"""
            try:
                response = self.llm.invoke(single_prompt)
                return extract_llm_content(response)
            except Exception as e:
                return f"Single paper synthesis failed: {str(e)}"

        # Multi-paper comparative synthesis
        formatted_papers = []
        for i, paper in enumerate(summaries, start=1):
            title = paper.get("title", "Unknown")
            source = paper.get("source", "Unknown")
            summary = truncate_text(paper.get("summary", ""), 2500)
            formatted_papers.append(
                f"### PAPER {i}: {title}\n"
                f"Source: {source}\n"
                f"Key Findings / Summary:\n{summary}\n"
            )

        paper_text = "\n".join(formatted_papers)

        prompt = f"""You are an expert scientific literature analyst.

Compare and synthesize the following {len(summaries)} research papers:

{paper_text}

Provide a comprehensive comparative analysis structured as follows:

1. Comparative Matrix & Key Objectives
   - What problems does each paper aim to solve?
2. Methodological Comparison
   - Contrasting techniques, architectures, and theoretical approaches.
3. Points of Agreement & Consensus
   - Shared conclusions and validated phenomena across papers.
4. Divergences, Contradictions & Trade-offs
   - Where results or assumptions differ, and underlying reasons.
5. Limitations & Vulnerabilities
   - Weaknesses acknowledged or evident across the studies.
6. Overall State of the Art
   - Summary of current advancements and where the field stands today.

Rely strictly on the provided paper summaries. Do not extrapolate unsupported claims.
"""

        try:
            response = self.llm.invoke(prompt)
            return extract_llm_content(response)
        except Exception as e:
            return f"Literature comparison failed: {str(e)}"
