# run_query.py
import argparse
import os
import sys
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from agentic_rag import AgenticRAG
from langchain_groq import ChatGroq


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run a scientific research query through the Agentic RAG pipeline."
    )
    parser.add_argument(
        "-q", "--query",
        type=str,
        help="The scientific research question to investigate. If omitted, you will be prompted."
    )
    parser.add_argument(
        "-k", "--top-k",
        type=int,
        default=3,
        help="Number of top ranked papers to analyze in detail (default: 3)."
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="research_report.md",
        help="Path where the final research report Markdown file will be saved (default: research_report.md)."
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        help="Groq LLM model name (default: openai/gpt-oss-120b)."
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Query input
    query = args.query
    if not query:
        print("\n" + "="*70)
        print("  Scientific Agentic RAG CLI")
        print("="*70)
        try:
            query = input("\nEnter your scientific research question:\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            sys.exit(0)

    if not query:
        print("Error: A non-empty research query is required.")
        sys.exit(1)

    # API key check
    if not os.getenv("GROQ_API_KEY"):
        print("Warning: GROQ_API_KEY environment variable is not set. Execution may fail.")

    print(f"\nInitializing Agentic RAG pipeline (Model: {args.model})...")
    
    try:
        llm = ChatGroq(
            model=args.model,
            temperature=0.1,
            max_tokens=4096
        )

        vector_db = None
        if os.path.exists("./chroma_db"):
            try:
                from langchain_huggingface import HuggingFaceEmbeddings
                from langchain_chroma import Chroma
                embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
                vector_db = Chroma(
                    collection_name="scientific_papers",
                    persist_directory="./chroma_db",
                    embedding_function=embeddings
                )
            except Exception as e:
                print(f"Notice: Chroma DB not loaded ({e}). Continuing with online literature sources.")

        agent = AgenticRAG(
            llm=llm,
            vector_db=vector_db,
            top_k_documents=args.top_k
        )

        print(f"\nAnalyzing research query: \"{query}\"")
        print("-" * 70)

        result = agent.run(query)

        if not result.get("success"):
            print(f"\nPipeline could not complete: {result.get('message')}")
            sys.exit(1)

        print("\n" + "="*70)
        print("  EXECUTION SUMMARY & METRICS")
        print("="*70)
        print(f"Total Execution Time : {result.get('total_time')} seconds")
        print(f"Documents Retrieved  : {len(result.get('retrieved_documents', []))}")
        print(f"Papers Synthesized   : {len(result.get('ranked_documents', []))}")
        
        print("\nLatency Breakdown:")
        for step, duration in result.get("timings", {}).items():
            print(f"  • {step.replace('_', ' ').title():<22} : {duration}s")

        # Save report
        report_content = result.get("report", "")
        if report_content:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report_content)
            print(f"\nFull scientific report successfully saved to: {args.output}")

        print("\n" + "="*70)
        print("  FINAL REPORT PREVIEW")
        print("="*70)
        print(report_content[:1500] + "\n\n...[Full report saved to disk]")

    except Exception as e:
        print(f"\nError running research query: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
