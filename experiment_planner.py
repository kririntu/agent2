# experiment_planner.py
from typing import Any, Dict, List, Optional
from utils import extract_llm_content, truncate_text


class ExperimentPlanner:
    """Translates identified research gaps into concrete, actionable

    experimental research plans.
    """

    def __init__(self, llm: Any):
        self.llm = llm

    def plan(
        self,
        gaps: str,
        comparison: str = "",
        evidence: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Create actionable research plans for identified gaps."""
        if not gaps or not str(gaps).strip():
            return "No research gaps were identified to formulate experimental plans."

        if evidence is None:
            evidence = []

        # Format literature evidence concisely to fit context window
        formatted_evidence = []
        for i, paper in enumerate(evidence, start=1):
            title = paper.get("title", "Unknown")
            source = paper.get("source", "Unknown")
            summary = paper.get("summary") or truncate_text(paper.get("content", ""), 1000)

            formatted_evidence.append(
                f"[Paper {i}]\n"
                f"Title: {title}\n"
                f"Source: {source}\n"
                f"Summary / Key Findings: {summary}\n"
            )

        evidence_text = "\n".join(formatted_evidence)
        safe_gaps = truncate_text(str(gaps), 8000)
        safe_comparison = truncate_text(str(comparison), 6000)

        prompt = f"""You are an expert scientific research planner and principal investigator.

Your task is to convert the identified research gaps into concrete, realistic, and scientifically rigorous research experiment plans.

IDENTIFIED RESEARCH GAPS:
{safe_gaps}

LITERATURE CONTEXT:
{safe_comparison}

RELEVANT CITATIONS / EVIDENCE:
{evidence_text}

For each major research gap, design an actionable experiment plan following this exact structure:

### Experiment Plan [Number]: [Descriptive Title]
1. Target Research Gap: Specific gap being addressed.
2. Research Question & Hypothesis: Testable hypothesis and core objective.
3. Proposed Methodology & Architecture: Step-by-step technical approach, algorithms, or framework.
4. Datasets, Benchmarks & Baselines: Data requirements, control groups, and state-of-the-art baselines for comparison.
5. Evaluation Metrics & Success Criteria: Quantitative and qualitative indicators of success.
6. Potential Risks & Mitigation Strategies: Expected failure modes or bottlenecks and how to handle them.
7. Estimated Scope & Feasibility: Expected computational resources and implementation complexity.

Provide rigorous, publication-grade research proposals.
"""

        try:
            response = self.llm.invoke(prompt)
            return extract_llm_content(response)
        except Exception as e:
            return f"Experiment planning failed: {str(e)}"
