# app.py
import os
from typing import Any, Dict, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agentic_rag import AgenticRAG

app = FastAPI(
    title="Scientific Agentic RAG API",
    description="Production-grade Agentic RAG for scientific literature discovery, synthesis, and research roadmap generation.",
    version="2.0.0"
)

# Enable CORS for Streamlit and web frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Request & Response Models
# ============================================================

class ResearchQuery(BaseModel):
    query: str = Field(..., min_length=2, description="The research question to analyze.")
    top_k: Optional[int] = Field(default=4, ge=1, le=10, description="Top ranked papers to analyze.")


# ============================================================
# Lazy / Resilient Engine Initialization
# ============================================================

_agent_instance: Optional[AgenticRAG] = None


def get_agent() -> AgenticRAG:
    """Initialize or retrieve the singleton AgenticRAG instance."""
    global _agent_instance
    if _agent_instance is not None:
        return _agent_instance

    # 1. Initialize LLM (Groq)
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("Warning: GROQ_API_KEY environment variable is not set. LLM calls may fail.")

    model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    try:
        from langchain_groq import ChatGroq
        llm = ChatGroq(
            model=model_name,
            temperature=0.1,
            max_tokens=4096,
            api_key=groq_api_key
        )
    except Exception as e:
        print(f"Error initializing ChatGroq with model {model_name}: {e}")
        raise RuntimeError(f"Failed to initialize ChatGroq: {e}")

    # 2. Initialize Vector Database (Optional / Resilient)
    vector_db = None
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_chroma import Chroma

        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        if os.path.exists(persist_dir):
            vector_db = Chroma(
                collection_name="scientific_papers",
                persist_directory=persist_dir,
                embedding_function=embeddings
            )
            print(f"Loaded Chroma vector DB from '{persist_dir}'.")
    except Exception as e:
        print(f"Notice: Chroma vector database not loaded ({e}). Proceeding with external literature sources.")

    # 3. Create Agentic RAG
    _agent_instance = AgenticRAG(
        llm=llm,
        vector_db=vector_db,
        sql_db=None,
        graph_db=None,
        top_k_documents=4
    )
    return _agent_instance


# ============================================================
# Endpoints
# ============================================================

@app.get("/")
def root():
    """Service status and meta info."""
    return {
        "status": "online",
        "service": "Scientific Agentic RAG API",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "research": "/research",
            "plan": "/plan"
        }
    }


@app.get("/health")
def health_check():
    """Detailed health check for all subsystem components."""
    try:
        agent = get_agent()
        active_sources = agent._get_available_sources()
        return {
            "status": "healthy",
            "model": os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            "active_sources": active_sources,
            "vector_db_connected": agent.vector_db is not None
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e)
        }


@app.post("/plan")
def inspect_plan(request: ResearchQuery):
    """Inspect the planned execution path for a given query without executing

    expensive LLM stages.
    """
    clean_q = request.query.strip()
    if not clean_q:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        agent = get_agent()
        available_sources = agent._get_available_sources()
        plan = agent.planner.create_plan(clean_q, available_sources=available_sources)
        return {
            "query": clean_q,
            "plan": plan
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planning error: {str(e)}")


@app.post("/research")
def research(request: ResearchQuery) -> Dict[str, Any]:
    """Execute the full agentic scientific literature discovery and synthesis

    pipeline.
    """
    clean_q = request.query.strip()
    if not clean_q:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        agent = get_agent()
        if request.top_k:
            agent.reranker.top_k = request.top_k

        result = agent.run(clean_q)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Research pipeline execution failed: {str(e)}"
        )
