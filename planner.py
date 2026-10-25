# planner.py
from typing import Any, Dict, List, Optional, Set


class Planner:
    """Analyzes user research queries to generate an optimal execution plan,

    selecting retrieval sources and analytical stages.
    """

    def __init__(self):
        pass

    def create_plan(
        self,
        query: str,
        available_sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate execution plan specifying retrieval sources and analytical

        steps.
        """
        q = (query or "").lower().strip()

        # If available_sources is specified, use it as a filter/whitelist
        has_filter = available_sources is not None
        allowed: Set[str] = set(available_sources) if has_filter else {
            "arxiv", "vector", "web", "wikipedia", "sql", "graph"
        }

        retrieval_sources: List[str] = []

        # 1. Structured SQL data queries
        if any(term in q for term in [
            "count", "average", "salary", "employee", "sales", "department", "table", "sql"
        ]) and "sql" in allowed:
            retrieval_sources.append("sql")

        # 2. Knowledge graph / relational queries
        if any(term in q for term in [
            "author", "co-author", "citation", "cites", "network", "connected", "graph"
        ]) and "graph" in allowed:
            retrieval_sources.append("graph")

        # 3. Conceptual / encyclopedic queries
        if any(term in q for term in [
            "who is", "what is", "history of", "invented", "biography", "definition", "overview"
        ]) and "wikipedia" in allowed:
            retrieval_sources.append("wikipedia")

        # 4. Recent / real-time / web queries
        if any(term in q for term in [
            "latest", "recent", "today", "news", "current", "2024", "2025", "2026", "online", "industry"
        ]) and "web" in allowed:
            retrieval_sources.append("web")

        # 5. Scientific literature (Default for scientific research)
        if "arxiv" in allowed:
            retrieval_sources.append("arxiv")

        # 6. Vector DB (Local documents / corpus)
        if "vector" in allowed:
            # If specifically asking about uploaded/local docs or alongside literature
            if any(term in q for term in ["local", "document", "internal", "stored", "vector", "pdf"]) or not retrieval_sources:
                retrieval_sources.append("vector")

        # Ensure at least one retrieval source is selected
        if not retrieval_sources:
            if "arxiv" in allowed:
                retrieval_sources.append("arxiv")
            elif "vector" in allowed:
                retrieval_sources.append("vector")
            elif "web" in allowed:
                retrieval_sources.append("web")
            else:
                retrieval_sources = list(allowed)[:1] if allowed else ["arxiv"]

        # Deduplicate while preserving order
        seen = set()
        deduped_sources = [s for s in retrieval_sources if not (s in seen or seen.add(s))]

        # Analytical steps
        analyze_steps: List[str] = ["summarize"]

        if any(x in q for x in [
            "compare", "difference", "versus", "vs", "contrast", "tradeoff", "benchmark"
        ]):
            analyze_steps.append("compare")

        if any(x in q for x in [
            "gap", "limitation", "open problem", "future work", "challenge", "unexplored", "weakness"
        ]):
            analyze_steps.append("gap")

        if any(x in q for x in [
            "experiment", "proposal", "research plan", "methodology", "hypothesis", "solve", "how to"
        ]):
            analyze_steps.append("experiment")

        # If user asked a comprehensive question, include full analytical pipeline
        if len(analyze_steps) == 1:
            # Default to full scientific discovery stack
            analyze_steps = ["summarize", "compare", "gap", "experiment"]

        # Determine target output format
        output_format = "report"
        if any(x in q for x in ["quick", "short", "simple", "direct", "brief", "just answer"]):
            output_format = "answer"
        elif "review" in q or "literature review" in q:
            output_format = "review"
        elif "proposal" in q:
            output_format = "proposal"

        return {
            "query": query,
            "retrieve": deduped_sources,
            "analyze": analyze_steps,
            "output": output_format
        }
