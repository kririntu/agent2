# test_all.py
import sys
try:
    import pytest
except ImportError:
    pytest = None
from unittest.mock import MagicMock, patch

from utils import (
    clean_text,
    truncate_text,
    format_documents,
    remove_duplicates,
    extract_llm_content,
    get_source,
    get_content
)
from planner import Planner
from retriever import Retriever
from reranker import Reranker
from summarizer import PaperSummarizer
from comparator import PaperComparator
from gap_detector import GapDetector
from experiment_planner import ExperimentPlanner
from reflection import ReflectionAgent
from report_generator import ReportGenerator
from agentic_rag import AgenticRAG
from agent import AgenticRAG as LightweightAgent


# ============================================================
# Dummy Mock LLM
# ============================================================

class DummyLLM:
    """Mock LLM that mimics LangChain ChatModel response."""
    def __init__(self, response_text="Mocked LLM generation."):
        self.response_text = response_text
        self.last_prompt = None

    def invoke(self, prompt):
        self.last_prompt = prompt
        mock_resp = MagicMock()
        mock_resp.content = self.response_text
        return mock_resp


# ============================================================
# 1. Tests for utils.py
# ============================================================

def test_clean_text():
    assert clean_text("  hello   world  \n\n test  ") == "hello world test"
    assert clean_text(None) == ""
    assert clean_text(123) == "123"
    # preserve_newlines
    multiline = "Para 1   with spaces.\n\n\n\nPara 2."
    cleaned = clean_text(multiline, preserve_newlines=True)
    assert "Para 1 with spaces." in cleaned
    assert "Para 2." in cleaned
    assert "\n\n\n" not in cleaned


def test_truncate_text():
    assert truncate_text("short", 10) == "short"
    assert truncate_text(None) == ""
    long_text = "a" * 100
    truncated = truncate_text(long_text, 10)
    assert len(truncated) > 10
    assert "...[truncated]" in truncated
    assert truncated.startswith("aaaaaaaaaa")


def test_format_documents():
    docs = [
        {"title": "Paper 1", "source": "arxiv", "content": "Content 1", "url": "http://arxiv.org/1"},
        {"title": "Paper 2", "source": "web", "content": "Content 2"}
    ]
    formatted = format_documents(docs)
    assert "Document 1" in formatted
    assert "Paper 1" in formatted
    assert "http://arxiv.org/1" in formatted
    assert "Document 2" in formatted


def test_remove_duplicates():
    docs = [
        {"title": "P1", "content": "Content A", "url": "http://url1"},
        {"title": "P1", "content": "Content A", "url": "http://url1"},  # duplicate by URL
        {"title": "P2", "content": "Content B"},
        {"title": "P2", "content": "Content B"}   # duplicate by content & title
    ]
    unique = remove_duplicates(docs)
    assert len(unique) == 2


def test_extract_llm_content():
    # String
    assert extract_llm_content("hello") == "hello"
    # None
    assert extract_llm_content(None) == ""
    # Object with .content string
    obj = MagicMock()
    obj.content = "from content"
    assert extract_llm_content(obj) == "from content"
    # Dict
    assert extract_llm_content({"content": "from dict"}) == "from dict"
    # List of parts
    obj_list = MagicMock()
    obj_list.content = ["part 1 ", {"text": "part 2"}]
    assert extract_llm_content(obj_list) == "part 1 part 2"


# ============================================================
# 2. Tests for planner.py
# ============================================================

def test_planner_routing():
    planner = Planner()

    # Arxiv / research query
    p1 = planner.create_plan("What are recent neural architectures in quantum chemistry?")
    assert "arxiv" in p1["retrieve"]
    assert "summarize" in p1["analyze"]

    # SQL query
    p2 = planner.create_plan("What is the average salary of employee in sales?")
    assert "sql" in p2["retrieve"]

    # Wikipedia query
    p3 = planner.create_plan("Who is Albert Einstein and history of relativity?")
    assert "wikipedia" in p3["retrieve"]

    # Comparative analysis query
    p4 = planner.create_plan("Compare transformer vs recurrent models")
    assert "compare" in p4["analyze"]

    # Available sources constraint
    p5 = planner.create_plan("Search query", available_sources=["arxiv", "vector"])
    for src in p5["retrieve"]:
        assert src in ["arxiv", "vector"]


# ============================================================
# 3. Tests for retriever.py
# ============================================================

def test_retriever_multi_source():
    mock_vector = MagicMock()
    mock_doc = MagicMock()
    mock_doc.page_content = "Vector doc text"
    mock_doc.metadata = {"title": "Local Paper"}
    mock_vector.similarity_search.return_value = [mock_doc]

    retriever = Retriever(vector_db=mock_vector)

    # Test vector retrieval
    res_vec = retriever.retrieve_vector("test query")
    assert len(res_vec) == 1
    assert res_vec[0]["source"] == "vector"
    assert res_vec[0]["title"] == "Local Paper"

    # Test concurrent retrieve()
    plan = {"retrieve": ["vector"]}
    results = retriever.retrieve("test query", plan)
    assert len(results) == 1


# ============================================================
# 4. Tests for reranker.py
# ============================================================

def test_reranker_fallback_and_ranking():
    reranker = Reranker(top_k=2)

    docs = [
        {"title": "Quantum Physics Basics", "content": "Introduction to quantum physics and entanglement."},
        {"title": "Cooking Pasta", "content": "How to boil water and make delicious tomato pasta."},
        {"title": "Quantum Computing", "content": "Qubits and quantum gate error correction in physics."}
    ]

    # Test with lexical ranking fallback directly
    ranked = reranker._fallback_lexical_rank("quantum physics", docs)
    assert len(ranked) == 2
    assert "Quantum" in ranked[0]["title"]

    # Test full rank() method
    results = reranker.rank("quantum entanglement", docs)
    assert len(results) <= 2
    for r in results:
        assert "relevance_score" in r


# ============================================================
# 5. Tests for summarizer.py
# ============================================================

def test_paper_summarizer():
    llm = DummyLLM("This paper introduces a novel optimization algorithm.")
    summarizer = PaperSummarizer(llm, max_workers=2)

    papers = [
        {"title": "Paper A", "source": "arxiv", "content": "Detailed text of Paper A..."},
        {"title": "Paper B", "source": "arxiv", "content": "Detailed text of Paper B..."}
    ]

    summaries = summarizer.summarize(papers)
    assert len(summaries) == 2
    assert summaries[0]["title"] == "Paper A"
    assert "novel optimization" in summaries[0]["summary"]


# ============================================================
# 6. Tests for comparator.py
# ============================================================

def test_comparator_single_and_multiple():
    llm = DummyLLM("Comparative analysis of the papers.")
    comparator = PaperComparator(llm)

    # Empty
    assert "No literature" in comparator.compare([])

    # Single paper (should synthesize, not fail!)
    single = [{"title": "P1", "source": "arxiv", "summary": "Summary of P1"}]
    res_single = comparator.compare(single)
    assert "Comparative analysis" in res_single

    # Multi papers
    multi = [
        {"title": "P1", "source": "arxiv", "summary": "Summary 1"},
        {"title": "P2", "source": "arxiv", "summary": "Summary 2"}
    ]
    res_multi = comparator.compare(multi)
    assert "Comparative analysis" in res_multi
    assert "PAPER 1" in llm.last_prompt
    assert "PAPER 2" in llm.last_prompt


# ============================================================
# 7. Tests for gap_detector.py
# ============================================================

def test_gap_detector_passes_comparison():
    llm = DummyLLM("Identified gaps: Lack of empirical validation on large datasets.")
    detector = GapDetector(llm)

    # Bug verification test: Comparison MUST be passed into prompt!
    comparison_text = "Paper A evaluated on 10 samples; Paper B evaluated on 20 samples."
    result = detector.detect(comparison_text)

    assert "Lack of empirical validation" in result
    assert comparison_text in llm.last_prompt  # Critical bug fix verification!


# ============================================================
# 8. Tests for experiment_planner.py
# ============================================================

def test_experiment_planner():
    llm = DummyLLM("Plan 1: Benchmark on ImageNet with ResNet50.")
    planner = ExperimentPlanner(llm)

    gaps = "Missing benchmarks on standard datasets."
    comparison = "Previous works only used synthetic data."
    evidence = [{"title": "Paper 1", "summary": "Synthetic data study"}]

    plan_output = planner.plan(gaps, comparison, evidence)
    assert "Plan 1" in plan_output
    assert gaps in llm.last_prompt
    assert "Synthetic data study" in llm.last_prompt


# ============================================================
# 9. Tests for reflection.py
# ============================================================

def test_reflection_agent():
    llm = DummyLLM("Critique: The proposed dataset size may be insufficient.")
    agent = ReflectionAgent(llm)

    critique = agent.review(
        query="Scalability of Model X",
        summaries=[{"title": "Paper X", "summary": "Evaluated on small cluster"}],
        comparison="Model X has high memory usage",
        gaps="No distributed implementation",
        research_plan="Test on single machine"
    )

    assert "insufficient" in critique
    assert "Model X has high memory usage" in llm.last_prompt
    assert "Paper X" in llm.last_prompt


# ============================================================
# 10. Tests for report_generator.py
# ============================================================

def test_report_generator():
    llm = DummyLLM("# Scientific Research Report: Advanced Scaling\n\n## 1. Executive Summary\nExcellent results.")
    generator = ReportGenerator(llm)

    report = generator.generate(
        query="Scaling laws of LLMs",
        summaries=[{"title": "P1", "summary": "Loss scales as power law"}],
        comparison="Agreement across models",
        gaps="Multimodal scaling remains unclear",
        research_plan="Experiment with 100B parameter vision-language model",
        reflection="High compute requirement is a risk"
    )

    assert "Scientific Research Report" in report
    assert "Loss scales as power law" in llm.last_prompt


# ============================================================
# 11. End-to-End Integration Test for AgenticRAG
# ============================================================

def test_agentic_rag_full_pipeline():
    llm = DummyLLM("Synthesized scientific analysis.")

    mock_vector = MagicMock()
    mock_doc = MagicMock()
    mock_doc.page_content = "Altermagnetism exhibit zero net magnetization with spin splitting."
    mock_doc.metadata = {"title": "Altermagnetic CrSb Study", "url": "https://arxiv.org/abs/test"}
    mock_vector.similarity_search.return_value = [mock_doc]

    agent = AgenticRAG(
        llm=llm,
        vector_db=mock_vector,
        top_k_documents=2
    )

    result = agent.run("What are the properties of altermagnetic CrSb in the stored documents?")

    assert result["success"] is True
    assert "report" in result
    assert "summaries" in result
    assert "research_gaps" in result
    assert "research_plan" in result
    assert "timings" in result
    assert "total_time" in result
    assert len(result["retrieved_documents"]) >= 1


# ============================================================
# 12. Lightweight Agent Test (agent.py)
# ============================================================

def test_lightweight_agent():
    llm = DummyLLM("Answer based on retrieved context.")
    mock_vector = MagicMock()
    mock_doc = MagicMock()
    mock_doc.page_content = "Einstein discovered relativity in 1905."
    mock_doc.metadata = {}
    mock_vector.similarity_search.return_value = [mock_doc]

    agent = LightweightAgent(
        llm=llm,
        vector_db=mock_vector
    )

    answer = agent.run("Explain relativity theory")
    assert "Answer based on retrieved context" in answer


# ============================================================
# 13. FastAPI app endpoint tests
# ============================================================

def test_fastapi_app():
    try:
        from fastapi.testclient import TestClient
        from app import app, _agent_instance
        import app as app_module
    except ImportError:
        print("  (Skipping test_fastapi_app: fastapi / testclient not installed)")
        return

    # Inject a mocked agent into the app module
    mock_agent = MagicMock()
    mock_agent._get_available_sources.return_value = ["arxiv", "vector"]
    mock_agent.planner.create_plan.return_value = {
        "retrieve": ["arxiv"],
        "analyze": ["summarize", "gap"],
        "output": "report"
    }
    mock_agent.run.return_value = {
        "success": True,
        "query": "Test query",
        "report": "Mocked full report"
    }
    app_module._agent_instance = mock_agent

    client = TestClient(app)

    # 1. Test root
    resp_root = client.get("/")
    assert resp_root.status_code == 200
    assert resp_root.json()["status"] == "online"

    # 2. Test health
    resp_health = client.get("/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["status"] == "healthy"

    # 3. Test plan
    resp_plan = client.post("/plan", json={"query": "Test quantum mechanics"})
    assert resp_plan.status_code == 200
    assert "plan" in resp_plan.json()

    # 4. Test research
    resp_res = client.post("/research", json={"query": "Test quantum mechanics", "top_k": 3})
    assert resp_res.status_code == 200
    assert resp_res.json()["success"] is True
    assert "Mocked full report" in resp_res.json()["report"]


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_") and callable(v)]
    passed, failed = 0, 0
    print(f"Running {len(tests)} test cases...")
    for test in tests:
        try:
            test()
            print(f"  ✓ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__}: {e}")
            failed += 1
    print(f"\nCompleted: {passed} passed, {failed} failed.")
    if failed:
        sys.exit(1)
