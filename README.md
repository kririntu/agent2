# 🔬 Scientific Agentic RAG

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Groq LPU](https://img.shields.io/badge/LLM-Groq%20LPU-orange.svg)](https://groq.com/)
[![LangChain](https://img.shields.io/badge/Framework-LangChain-1C3C3C.svg)](https://www.langchain.com/)

**Scientific Agentic RAG** is an autonomous, multi-stage research agent designed for deep scientific literature discovery, cross-paper comparative synthesis, research gap detection, peer reflection review, and publication-ready experimental roadmap generation.

Powered by **Groq LPU** inference and **LangChain**, it combines multi-source retrieval (ArXiv, Wikipedia, DuckDuckGo, ChromaDB), neural semantic reranking, and specialized analytical agents to turn complex research inquiries into comprehensive scientific surveys.

---

## 📑 Table of Contents

- [Key Features](#-key-features)
- [Pipeline Architecture](#-pipeline-architecture)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Setup](#environment-setup)
- [Usage Modes](#-usage-modes)
  - [1. Interactive CLI](#1-interactive-cli)
  - [2. Streamlit Web Dashboard](#2-streamlit-web-dashboard)
  - [3. FastAPI REST Server](#3-fastapi-rest-server)
  - [4. Python SDK Import](#4-python-sdk-import)
- [API Documentation](#-api-documentation)
- [Configuration Reference](#-configuration-reference)
- [Running Tests](#-running-tests)
- [Example Output](#-example-output)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚀 Key Features

- **Multi-Source Retrieval Engine**: Parallel querying across academic repositories (ArXiv), encyclopedic sources (Wikipedia), web search (DuckDuckGo), local vector databases (ChromaDB), SQL databases, and knowledge graphs.
- **Neural Semantic Reranking**: Re-orders retrieved literature using `SentenceTransformer` embeddings (`all-MiniLM-L6-v2`) with graceful lexical keyword fallbacks.
- **Concurrent Paper Summarization**: Multi-threaded extraction of core problems, methodologies, empirical results, acknowledged limitations, and open questions.
- **Comparative Literature Synthesis**: Evaluates agreements, contradictions, and methodological divergences across multiple studies.
- **Automated Research Gap Detection**: Rigorously categorizes gaps into Methodological, Empirical/Dataset, Theoretical, and Practical/Scalability opportunities.
- **Actionable Experiment Planning**: Translates identified gaps into concrete experimental protocols, baseline comparisons, evaluation metrics, and expected risks.
- **Senior Peer-Review Reflection**: An adversarial critique agent audits claims, assesses methodological feasibility, and flags potential oversights.
- **Publication-Grade Report Generation**: Outputs polished Markdown reports structured like formal scientific review surveys.

---

## 🏗 Pipeline Architecture

```
                       ┌───────────────────────────┐
                       │    User Research Query    │
                       └─────────────┬─────────────┘
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │     1. Query Planner      │
                       │ selects sources & stages  │
                       └─────────────┬─────────────┘
                                     │
                                     ▼
                ┌─────────────────────────────────────────┐
                │        2. Multi-Source Retriever        │
                ├───────────┬───────────┬───────────┬─────┤
                │   ArXiv   │ Wikipedia │  Web/DDGS │ VDB │
                └─────┬─────┴─────┬─────┴─────┬─────┴──┬──┘
                      └───────────┼───────────┘        │
                                  ▼                    │
                       ┌───────────────────────────┐   │
                       │   Deduplication Layer     │◄──┘
                       └─────────────┬─────────────┘
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │    3. Neural Reranker     │
                       │ (Sentence Transformers)   │
                       └─────────────┬─────────────┘
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │   4. Paper Summarizer     │
                       │   (Concurrent Extraction) │
                       └─────────────┬─────────────┘
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │ 5. Comparative Synthesis  │
                       └─────────────┬─────────────┘
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │   6. Gap Detector Agent   │
                       └─────────────┬─────────────┘
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │ 7. Experiment Planner     │
                       └─────────────┬─────────────┘
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │  8. Reflection Reviewer   │
                       │    (Peer Audit Agent)     │
                       └─────────────┬─────────────┘
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │ 9. Final Report Generator │
                       └─────────────┬─────────────┘
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │ Publication-Ready Survey  │
                       └───────────────────────────┘
```

---

## 📂 Project Structure

```text
├── agentic_rag.py         # Complete multi-agent pipeline orchestrator
├── agent.py               # Lightweight standalone Agentic RAG implementation
├── app.py                 # FastAPI backend service & REST endpoints
├── streamlit.py           # Interactive Streamlit web interface
├── run_query.py           # Command-line query runner (CLI)
├── planner.py             # Query intent classifier and source router
├── retriever.py           # Concurrent multi-source literature retriever
├── reranker.py            # Neural & lexical document reranking
├── summarizer.py          # Concurrent structured paper summarizer
├── comparator.py          # Cross-paper comparative synthesis agent
├── gap_detector.py        # Scientific gap detection agent
├── experiment_planner.py  # Actionable experiment & roadmap planner
├── reflection.py          # Critical peer reviewer & methodology auditor
├── report_generator.py    # Publication-grade Markdown report generator
├── utils.py               # Text normalization, deduplication & helpers
├── test_all.py            # Comprehensive test suite (unit & integration)
├── nb_ir_te4_survey.md    # Sample scientific survey generated by the pipeline
├── requirements.txt       # Project dependencies
├── .env.example           # Environment variable template
├── .gitignore             # Git ignore patterns
└── LICENSE                # MIT License
```

---

## ⚡ Quick Start

### Prerequisites

- Python `3.10` or higher
- A Groq Cloud API Key ([Get one free at Groq Console](https://console.groq.com/keys))

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/scientific-agentic-rag.git
   cd scientific-agentic-rag
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   # On Windows: .venv\Scripts\activate
   ```

3. **Install required dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### Environment Setup

Copy `.env.example` to `.env` and set your Groq API key:

```bash
cp .env.example .env
```

Edit `.env`:
```ini
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
CHROMA_PERSIST_DIR=./chroma_db
```

---

## 💻 Usage Modes

### 1. Interactive CLI

Run research queries directly from your terminal:

```bash
# Provide query as an argument:
python run_query.py -q "What are the current research gaps in altermagnetic CrSb?" -k 4 -o altermagnetism_report.md

# Or start interactive mode:
python run_query.py
```

**CLI Flags:**
- `-q`, `--query`: Scientific research question.
- `-k`, `--top-k`: Number of top-ranked papers to analyze (default: `3`).
- `-o`, `--output`: Path to save the Markdown report (default: `research_report.md`).
- `-m`, `--model`: Groq model override (default: `openai/gpt-oss-120b`).

---

### 2. Streamlit Web Dashboard

Launch the graphical user interface:

```bash
streamlit run streamlit.py
```

Open your browser at `http://localhost:8501`. The dashboard allows you to:
- Select between **FastAPI Server** or **In-Process Direct** execution.
- Click sample research queries or type custom prompts.
- Track real-time progress through all 9 pipeline steps.
- Inspect raw literature summaries, comparative tables, detected gaps, and experiment plans.
- Download the generated report as Markdown.

---

### 3. FastAPI REST Server

Start the RESTful backend:

```bash
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Access the interactive Swagger API documentation at:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

---

### 4. Python SDK Import

Integrate the agent into your own Python applications:

```python
import os
from langchain_groq import ChatGroq
from agentic_rag import AgenticRAG

# Initialize Groq LLM
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1
)

# Initialize Agentic RAG
agent = AgenticRAG(llm=llm, top_k_documents=4)

# Execute research pipeline
result = agent.run("Topological and transport phenomena in NbIrTe4")

if result["success"]:
    print(result["report"])
    print(f"Total execution time: {result['total_time']}s")
```

---

## 📡 API Documentation

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | API status and endpoint directory |
| `GET` | `/health` | Subsystem health check (LLM, active sources, vector DB status) |
| `POST` | `/plan` | Previews the execution plan without triggering LLM calls |
| `POST` | `/research` | Executes the complete 9-stage research workflow |

### Example Request (`POST /research`):

```bash
curl -X POST "http://127.0.0.1:8000/research" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Quantum error correction with surface codes open challenges",
       "top_k": 3
     }'
```

---

## ⚙️ Configuration Reference

All settings can be configured via environment variables or a `.env` file:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | *(Required)* | Groq API key for LLM inference |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Target LLM model hosted on Groq |
| `CHROMA_PERSIST_DIR` | `./chroma_db` | Storage path for local ChromaDB vector store |
| `FASTAPI_HOST` | `127.0.0.1` | Binding host for FastAPI server |
| `FASTAPI_PORT` | `8000` | Port for FastAPI server |
| `STREAMLIT_PORT` | `8501` | Port for Streamlit dashboard |

---

## 🧪 Running Tests

The test suite covers text normalization, query planning, multi-source retrieval, reranking, all analytical agents, end-to-end pipeline execution, and REST endpoints:

```bash
# Run with pytest (verbose output)
pytest test_all.py -v

# Or run directly with standard Python:
python3 test_all.py
```

---

## 📄 Example Output

Check out [`nb_ir_te4_survey.md`](nb_ir_te4_survey.md) in this repository for a complete sample report produced by the agent on:
> *"Topological and Transport Phenomena in NbIrTe₄ – A Comprehensive Survey and Roadmap Toward Resolving Open Challenges"*

---

## 🤝 Contributing

Contributions, bug reports, and feature requests are welcome!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for details.
