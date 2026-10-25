# gap_detector.py
from typing import Any
from utils import extract_llm_content, truncate_text


class GapDetector:
    """Detects research gaps from a literature comparison or summaries."""

    def __init__(self, llm: Any):
        self.llm = llm

    def detect(self, comparison: str) -> str:
        """Analyze literature comparison to identify open research gaps."""
        if not comparison or not str(comparison).strip():
            return "No literature comparison available to detect research gaps."

        # Truncate comparison safely to avoid token limit overflow
        safe_comparison = truncate_text(str(comparison), max_length=12000)

        prompt = f"""You are an expert scientific research analyst.

You are given a comprehensive synthesis/comparison of research papers in a specific domain.

LITERATURE COMPARISON:
{safe_comparison}

Your task is to identify and structure clear, actionable RESEARCH GAPS based strictly on the literature provided above.
Do not hallucinate or assume unmentioned experiments.

Please organize the research gaps into the following categories:

1. Methodological & Algorithmic Gaps
   - Limitations in current approaches, models, or techniques.

2. Empirical & Dataset Gaps
   - Missing benchmarks, domain-specific evaluation, or unverified scenarios.

3. Theoretical & Analytical Gaps
   - Unexplored mechanisms, lacking theoretical foundations, or conflicting explanations.

4. Practical & Scalability Gaps
   - Real-world deployment challenges, efficiency bottlenecks, or edge cases.

5. Priority Gaps for Immediate Future Research
   - Top 2-3 most promising high-impact directions that should be tackled first.

Be precise, concrete, and rigorous in your analysis.
"""

        try:
            response = self.llm.invoke(prompt)
            return extract_llm_content(response)
        except Exception as e:
            return f"Research gap detection failed: {str(e)}"
