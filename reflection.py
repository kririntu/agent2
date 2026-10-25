# reflection.py
import time
from typing import Any, Dict, List, Optional
from utils import extract_llm_content, truncate_text

try:
    from groq import RateLimitError
except ImportError:
    class RateLimitError(Exception):
        """Fallback exception class if groq is not installed."""
        pass


class ReflectionAgent:
    """Critically evaluates research synthesis, identifying logical fallacies,

    unsupported claims, and methodological weaknesses.
    """

    def __init__(self, llm: Any, max_retries: int = 3):
        self.llm = llm
        self.max_retries = max_retries

    def review(
        self,
        query: str,
        summaries: Optional[List[Dict[str, Any]]] = None,
        comparison: Optional[str] = "",
        gaps: Optional[str] = "",
        research_plan: Optional[str] = ""
    ) -> str:
        """Conduct a critical review of the synthesized literature and proposals."""
        safe_query = str(query or "")
        safe_comparison = truncate_text(str(comparison or ""), max_length=3000)
        safe_gaps = truncate_text(str(gaps or ""), max_length=2000)
        safe_plan = truncate_text(str(research_plan or ""), max_length=2000)

        # Summarize paper evidence if provided
        evidence_snippets = []
        if summaries:
            for s in summaries[:5]:
                t = s.get("title", "Unknown")
                summ = truncate_text(s.get("summary", ""), 300)
                evidence_snippets.append(f"- {t}: {summ}")
        evidence_text = "\n".join(evidence_snippets) if evidence_snippets else "No raw summaries provided."

        prompt = f"""You are a senior peer reviewer and scientific methodology auditor.

Critically evaluate this research analysis and experimental proposal for accuracy, feasibility, and scientific validity.

USER RESEARCH QUESTION:
{safe_query}

LITERATURE EVIDENCE BASE:
{evidence_text}

LITERATURE COMPARISON:
{safe_comparison}

IDENTIFIED RESEARCH GAPS:
{safe_gaps}

PROPOSED RESEARCH PLAN:
{safe_plan}

Provide a rigorous critique addressing:
1. Unsupported or Overclaimed Conclusions: Are any claims not backed by the cited literature?
2. Gap Quality & Novelty: Are the identified gaps genuine, significant, and clearly framed?
3. Methodological Flaws or Blindspots: Any missing controls, problematic assumptions, or benchmark selection issues?
4. Technical Feasibility & Resource Constraints: Are the proposed experiments realistic?
5. Recommendations for Strengthening: Specific, constructive adjustments to solidify this research.

Be concise, constructive, and uncompromisingly rigorous.
"""

        for attempt in range(self.max_retries):
            try:
                response = self.llm.invoke(prompt)
                return extract_llm_content(response)

            except RateLimitError as e:
                if attempt < self.max_retries - 1:
                    sleep_time = 5 * (attempt + 1)
                    print(f"Rate limit reached. Retrying in {sleep_time}s... (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(sleep_time)
                else:
                    return f"Critical reflection paused due to persistent rate limiting: {str(e)}"

            except Exception as e:
                err_msg = str(e).lower()
                if "rate limit" in err_msg or "429" in err_msg:
                    if attempt < self.max_retries - 1:
                        sleep_time = 5 * (attempt + 1)
                        print(f"Rate limit detected. Retrying in {sleep_time}s... (attempt {attempt + 1}/{self.max_retries})")
                        time.sleep(sleep_time)
                        continue
                return f"Reflection step encountered an error: {str(e)}"

        return "Reflection failed after maximum retries."
