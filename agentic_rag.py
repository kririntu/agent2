# agentic_rag.py
import time
from typing import Any, Callable, Dict, List, Optional

from comparator import PaperComparator
from experiment_planner import ExperimentPlanner
from gap_detector import GapDetector
from planner import Planner
from reflection import ReflectionAgent
from report_generator import ReportGenerator
from reranker import Reranker
from retriever import Retriever
from summarizer import PaperSummarizer
from utils import remove_duplicates


class AgenticRAG:
    """Full-lifecycle Agentic RAG pipeline for scientific literature discovery,

    comparative synthesis, research gap detection, and experiment planning.
    """

    def __init__(
        self,
        llm: Any,
        vector_db: Optional[Any] = None,
        sql_db: Optional[Any] = None,
        graph_db: Optional[Any] = None,
        reranker_model: str = "all-MiniLM-L6-v2",
        top_k_documents: int = 4
    ):
        self.llm = llm
        self.vector_db = vector_db
        self.sql_db = sql_db
        self.graph_db = graph_db

        self.planner = Planner()
        self.retriever = Retriever(
            vector_db=vector_db,
            sql_db=sql_db,
            graph_db=graph_db
        )
        self.reranker = Reranker(
            model_name=reranker_model,
            top_k=top_k_documents
        )
        self.summarizer = PaperSummarizer(llm)
        self.comparator = PaperComparator(llm)
        self.gap_detector = GapDetector(llm)
        self.experiment_planner = ExperimentPlanner(llm)
        self.reflection = ReflectionAgent(llm)
        self.report_generator = ReportGenerator(llm)

    def _get_available_sources(self) -> List[str]:
        """Detect which database connectors are currently active."""
        sources = ["arxiv", "web", "wikipedia"]
        if self.vector_db is not None:
            sources.append("vector")
        if self.sql_db is not None:
            sources.append("sql")
        if self.graph_db is not None:
            sources.append("graph")
        return sources

    def run(
        self,
        query: str,
        callback: Optional[Callable[[str, Any], None]] = None
    ) -> Dict[str, Any]:
        """Execute the complete agentic research workflow.

        Args:
            query: The scientific research question.
            callback: Optional status update callable taking (step_name, data).

        Returns:
            Dictionary with full report, intermediate outputs, and execution metrics.
        """
        start_time = time.time()
        timings: Dict[str, float] = {}

        def notify(step: str, data: Any = None):
            if callback:
                try:
                    callback(step, data)
                except Exception:
                    pass

        # Step 1. Plan
        t0 = time.time()
        print("\n[Step 1] Planning execution...")
        notify("planning_start")

        available_sources = self._get_available_sources()
        plan = self.planner.create_plan(query, available_sources=available_sources)
        timings["planning"] = round(time.time() - t0, 3)
        print(f"  Plan: Sources={plan.get('retrieve')}, Analysis={plan.get('analyze')}")
        notify("planning_done", plan)

        # Step 2. Retrieve
        t0 = time.time()
        print("\n[Step 2] Retrieving literature...")
        notify("retrieval_start")

        results = self.retriever.retrieve(query=query, plan=plan)

        # Fallback if primary sources yielded nothing
        if not results:
            print("  Primary retrieval returned 0 results. Attempting fallback to Web & Wikipedia...")
            fallback_plan = {"retrieve": ["web", "wikipedia"]}
            results = self.retriever.retrieve(query=query, plan=fallback_plan)

        # Deduplicate retrieved documents
        results = remove_duplicates(results)
        timings["retrieval"] = round(time.time() - t0, 3)
        print(f"  Retrieved {len(results)} unique documents in {timings['retrieval']}s.")
        notify("retrieval_done", {"count": len(results)})

        if not results:
            return {
                "success": False,
                "query": query,
                "plan": plan,
                "message": "No relevant scientific documents were found across available sources.",
                "timings": timings,
                "total_time": round(time.time() - start_time, 3)
            }

        # Step 3. Rerank
        t0 = time.time()
        print("\n[Step 3] Reranking documents...")
        notify("rerank_start")

        ranked_results = self.reranker.rank(query=query, results=results)
        timings["reranking"] = round(time.time() - t0, 3)
        print(f"  Retained top {len(ranked_results)} ranked documents.")
        notify("rerank_done", ranked_results)

        # Step 4. Summarize (Concurrent)
        t0 = time.time()
        print("\n[Step 4] Summarizing papers...")
        notify("summarize_start")

        summaries = self.summarizer.summarize(ranked_results)
        timings["summarization"] = round(time.time() - t0, 3)
        print(f"  Summarized {len(summaries)} papers in {timings['summarization']}s.")
        notify("summarize_done", summaries)

        # Step 5. Compare & Synthesize
        t0 = time.time()
        print("\n[Step 5] Comparing literature...")
        notify("compare_start")

        comparison = self.comparator.compare(summaries)
        timings["comparison"] = round(time.time() - t0, 3)
        print(f"  Literature comparison completed in {timings['comparison']}s.")
        notify("compare_done", comparison)

        # Step 6. Detect Research Gaps
        t0 = time.time()
        print("\n[Step 6] Detecting research gaps...")
        notify("gap_detection_start")

        gaps = self.gap_detector.detect(comparison)
        timings["gap_detection"] = round(time.time() - t0, 3)
        print(f"  Research gaps detected in {timings['gap_detection']}s.")
        notify("gap_detection_done", gaps)

        # Step 7. Plan Future Research / Experiments
        t0 = time.time()
        print("\n[Step 7] Formulating research plans...")
        notify("experiment_planning_start")

        research_plan = self.experiment_planner.plan(
            gaps=gaps,
            comparison=comparison,
            evidence=ranked_results
        )
        timings["experiment_planning"] = round(time.time() - t0, 3)
        print(f"  Research plan created in {timings['experiment_planning']}s.")
        notify("experiment_planning_done", research_plan)

        # Step 8. Critical Reflection
        t0 = time.time()
        print("\n[Step 8] Critically reviewing analysis & proposals...")
        notify("reflection_start")

        reflection = self.reflection.review(
            query=query,
            summaries=summaries,
            comparison=comparison,
            gaps=gaps,
            research_plan=research_plan
        )
        timings["reflection"] = round(time.time() - t0, 3)
        print(f"  Reflection completed in {timings['reflection']}s.")
        notify("reflection_done", reflection)

        # Step 9. Generate Final Publication Report
        t0 = time.time()
        print("\n[Step 9] Generating final comprehensive report...")
        notify("report_start")

        report = self.report_generator.generate(
            query=query,
            summaries=summaries,
            comparison=comparison,
            gaps=gaps,
            research_plan=research_plan,
            reflection=reflection
        )
        timings["report_generation"] = round(time.time() - t0, 3)
        print(f"  Final report generated in {timings['report_generation']}s.")
        notify("report_done", report)

        total_time = round(time.time() - start_time, 3)
        print(f"\n[Done] Pipeline finished successfully in {total_time}s.")

        return {
            "success": True,
            "query": query,
            "plan": plan,
            "retrieved_documents": results,
            "ranked_documents": ranked_results,
            "summaries": summaries,
            "comparison": comparison,
            "research_gaps": gaps,
            "research_plan": research_plan,
            "reflection": reflection,
            "report": report,
            "timings": timings,
            "total_time": total_time
        }
