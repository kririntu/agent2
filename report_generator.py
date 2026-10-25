# report_generator.py
from typing import Any, Dict, List, Optional
from utils import extract_llm_content, truncate_text


class ReportGenerator:
    """Generates a cohesive, publication-grade scientific research report

    synthesizing all analysis stages.
    """

    def __init__(self, llm: Any):
        self.llm = llm

    def generate(
        self,
        query: str,
        summaries: Optional[Any] = None,
        comparison: Optional[Any] = None,
        gaps: Optional[Any] = None,
        research_plan: Optional[Any] = None,
        reflection: Optional[Any] = None
    ) -> str:
        """Synthesize all research elements into a structured final report."""
        # Format summaries if given as list of dicts
        summaries_text = ""
        if isinstance(summaries, list):
            formatted = []
            for s in summaries:
                if isinstance(s, dict):
                    formatted.append(f"- **{s.get('title', 'Unknown')}**: {s.get('summary', '')}")
                else:
                    formatted.append(str(s))
            summaries_text = "\n".join(formatted)
        else:
            summaries_text = str(summaries or "None provided.")

        safe_query = str(query or "")
        safe_summaries = truncate_text(summaries_text, 3500)
        safe_comparison = truncate_text(str(comparison or "None provided."), 3500)
        safe_gaps = truncate_text(str(gaps or "None provided."), 2500)
        safe_plan = truncate_text(str(research_plan or "None provided."), 2500)
        safe_reflection = truncate_text(str(reflection or "None provided."), 2000)

        prompt = f"""You are a principal research scientist preparing a comprehensive, publication-ready literature review and research roadmap.

Generate a comprehensive, scientifically rigorous research report based on the provided analysis.

USER RESEARCH QUESTION:
{safe_query}

PAPER SUMMARIES:
{safe_summaries}

LITERATURE COMPARISON & SYNTHESIS:
{safe_comparison}

IDENTIFIED RESEARCH GAPS:
{safe_gaps}

PROPOSED EXPERIMENTAL PLANS:
{safe_plan}

CRITICAL REFLECTION & PEER REVIEW:
{safe_reflection}

Format the report in elegant, well-structured GitHub-flavored Markdown using the following structure:

# Scientific Research Report: [Generate an Appropriate Title based on Query]

## 1. Executive Summary
Brief high-level synthesis of findings and primary takeaways.

## 2. Research Background & Problem Statement
Contextualize the user's research question within the current scientific domain.

## 3. Literature Synthesis & Comparative Analysis
Integrate the reviewed studies, contrasting methodologies, agreements, and discrepancies.

## 4. Key Findings & Current State of the Art
Synthesized findings, validated claims, and current technological limits.

## 5. Identified Research Gaps & Open Challenges
Categorized breakdown of existing gaps in the literature.

## 6. Proposed Research Roadmap & Experimental Methodology
Actionable research proposals addressing the top gaps, including hypotheses, methodology, and metrics.

## 7. Critical Evaluation, Risks & Mitigation
Peer review reflection addressing assumptions, feasibility constraints, and failure modes.

## 8. Conclusion & Strategic Next Steps
Final concluding remarks and prioritized action items.

Ensure all assertions cite the underlying literature context. Do not invent citations or empirical results.
"""

        try:
            response = self.llm.invoke(prompt)
            return extract_llm_content(response)

        except Exception as e:
            return (
                f"# Research Report Generation Error\n\n"
                f"An error occurred while compiling the final report: `{str(e)}`\n\n"
                f"### Preserved Synthesis Data\n\n"
                f"**Identified Gaps:**\n{safe_gaps}\n\n"
                f"**Research Plan:**\n{safe_plan}"
            )


if __name__ == "__main__":
    print("ReportGenerator module loaded successfully.")
