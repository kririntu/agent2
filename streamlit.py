# streamlit.py
import os
import time
import requests
import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ============================================================
# Page configuration
# ============================================================

st.set_page_config(
    page_title="Scientific Agentic RAG",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished scientific styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 12px;
        border-left: 4px solid #4A90E2;
        margin-bottom: 10px;
    }
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        background-color: #e9ecef;
        margin-right: 5px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# Sidebar Configuration
# ============================================================

st.sidebar.title("⚙️ Configuration")

api_url = st.sidebar.text_input(
    "API Server Endpoint:",
    value="http://127.0.0.1:8000",
    help="FastAPI backend URL"
)

top_k = st.sidebar.slider(
    "Top Ranked Papers to Analyze:",
    min_value=2,
    max_value=6,
    value=4,
    help="Number of most relevant papers to analyze deeply"
)

execution_mode = st.sidebar.radio(
    "Execution Mode:",
    ["API Server (FastAPI)", "In-Process (Direct)"],
    help="Choose whether to call the FastAPI backend or run the pipeline directly inside Streamlit."
)

st.sidebar.markdown("---")
st.sidebar.subheader("💡 Example Queries")
example_queries = [
    "What are the current research gaps in altermagnetic CrSb?",
    "Recent advances and limitations in Quantum Error Correction with Surface Codes",
    "Transformer architecture optimizations for edge device inference",
    "Mechanisms of action and open challenges in mRNA cancer vaccines"
]

for ex in example_queries:
    if st.sidebar.button(ex, key=f"ex_{ex[:15]}"):
        st.session_state["query_input"] = ex


# ============================================================
# Helper Functions
# ============================================================

@st.cache_resource(show_spinner=False)
def get_local_agent():
    """Lazily initialize the local AgenticRAG instance if running in in-process mode."""
    from agentic_rag import AgenticRAG
    from langchain_groq import ChatGroq

    model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    llm = ChatGroq(
        model=model_name,
        temperature=0.1,
        max_tokens=4096
    )

    vector_db = None
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_chroma import Chroma
        if os.path.exists("./chroma_db"):
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vector_db = Chroma(
                collection_name="scientific_papers",
                persist_directory="./chroma_db",
                embedding_function=embeddings
            )
    except Exception:
        pass

    return AgenticRAG(
        llm=llm,
        vector_db=vector_db,
        top_k_documents=top_k
    )


# ============================================================
# Main Content
# ============================================================

st.title("🔬 Scientific Agentic RAG")
st.caption("Autonomous scientific literature discovery, comparative synthesis, research gap detection, and experiment planning.")

# Query Input
default_val = st.session_state.get("query_input", "")
query = st.text_area(
    "Enter your scientific research question:",
    value=default_val,
    placeholder="e.g. What are the key bottlenecks and open problems in solid-state battery electrolytes?",
    height=110
)

col1, col2 = st.columns([1, 5])
with col1:
    run_clicked = st.button("🚀 Run Research", type="primary", use_container_width=True)
with col2:
    if st.button("🗑️ Clear Results", use_container_width=False):
        if "research_result" in st.session_state:
            del st.session_state["research_result"]
        st.rerun()


# ============================================================
# Pipeline Execution
# ============================================================

if run_clicked:
    clean_q = query.strip()
    if not clean_q:
        st.warning("Please enter a research question before running.")
    else:
        with st.spinner("Agentic RAG is executing autonomous literature discovery & scientific synthesis..."):
            result = None
            try:
                if execution_mode == "API Server (FastAPI)":
                    resp = requests.post(
                        f"{api_url.rstrip('/')}/research",
                        json={"query": clean_q, "top_k": top_k},
                        timeout=300
                    )
                    if resp.status_code == 200:
                        result = resp.json()
                    else:
                        st.error(f"API Error ({resp.status_code}): {resp.text}")
                else:
                    agent = get_local_agent()
                    agent.reranker.top_k = top_k
                    result = agent.run(clean_q)

            except requests.exceptions.ConnectionError:
                st.error(f"Could not connect to FastAPI at `{api_url}`. Start the server (`uvicorn app:app --port 8000`) or switch to 'In-Process (Direct)' mode in the sidebar.")
            except Exception as e:
                st.error(f"Execution Error: {str(e)}")

            if result:
                st.session_state["research_result"] = result


# ============================================================
# Display Results
# ============================================================

if "research_result" in st.session_state:
    res = st.session_state["research_result"]

    if not res.get("success", False):
        st.warning(res.get("message", "Pipeline did not find sufficient relevant literature."))
    else:
        st.success("Research synthesis and proposal generation complete!")

        # Key Metrics Row
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        with mcol1:
            total_t = res.get("total_time", "N/A")
            st.metric("Total Execution Time", f"{total_t}s" if isinstance(total_t, (int, float)) else total_t)
        with mcol2:
            num_retrieved = len(res.get("retrieved_documents", []))
            st.metric("Documents Retrieved", num_retrieved)
        with mcol3:
            num_ranked = len(res.get("ranked_documents", []))
            st.metric("Analyzed Papers (Top-K)", num_ranked)
        with mcol4:
            plan = res.get("plan", {})
            sources_str = ", ".join(plan.get("retrieve", ["arxiv"]))
            st.metric("Sources Queried", sources_str)

        # Download Report Button
        report_md = res.get("report", "")
        if report_md:
            st.download_button(
                label="📥 Download Full Research Report (.md)",
                data=report_md,
                file_name="scientific_research_report.md",
                mime="text/markdown"
            )

        # Tabbed Layout for Detailed Exploration
        tab_report, tab_gaps, tab_plan, tab_reflection, tab_comparison, tab_papers, tab_timings = st.tabs([
            "📄 Final Report",
            "🔎 Research Gaps",
            "🧪 Experiment Plans",
            "🧠 Peer Review Reflection",
            "📚 Literature Comparison",
            "📑 Retrieved Papers",
            "⏱️ Execution Timings"
        ])

        with tab_report:
            st.markdown(report_md)

        with tab_gaps:
            st.subheader("Identified Research Gaps")
            st.markdown(res.get("research_gaps", "No gaps identified."))

        with tab_plan:
            st.subheader("Actionable Experimental Research Plans")
            st.markdown(res.get("research_plan", "No research plan generated."))

        with tab_reflection:
            st.subheader("Critical Peer Review & Methodological Reflection")
            st.markdown(res.get("reflection", "No reflection generated."))

        with tab_comparison:
            st.subheader("Cross-Literature Comparative Synthesis")
            st.markdown(res.get("comparison", "No comparison generated."))

        with tab_papers:
            st.subheader("Top Ranked Literature Documents")
            ranked_docs = res.get("ranked_documents", [])
            if not ranked_docs:
                st.info("No documents ranked.")
            else:
                for idx, doc in enumerate(ranked_docs, start=1):
                    score = doc.get("relevance_score")
                    score_str = f" • Similarity: {score:.3f}" if score is not None else ""
                    source_str = doc.get("source", "Unknown").upper()
                    title_str = doc.get("title", f"Document {idx}")
                    url_str = doc.get("url", "")

                    with st.expander(f"[{source_str}] {title_str}{score_str}"):
                        if url_str:
                            st.markdown(f"🔗 **Link:** [{url_str}]({url_str})")
                        if "authors" in doc and doc["authors"]:
                            st.markdown(f"👥 **Authors:** {', '.join(doc['authors'])}")
                        if "published" in doc and doc["published"]:
                            st.markdown(f"📅 **Published:** {doc['published']}")
                        st.markdown("**Content Preview:**")
                        st.write(doc.get("content", ""))

        with tab_timings:
            st.subheader("Pipeline Latency Breakdown")
            timings = res.get("timings", {})
            if timings:
                for step_name, duration in timings.items():
                    col_s, col_d = st.columns([3, 1])
                    with col_s:
                        st.write(f"**{step_name.replace('_', ' ').title()}**")
                    with col_d:
                        st.write(f"`{duration}s`")
            else:
                st.info("Timing metrics unavailable.")
