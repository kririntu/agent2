# agent.py
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from typing import Any, Dict, List, Optional
from utils import extract_llm_content, remove_duplicates

# Resilient DDGS import
try:
    from duckduckgo_search import DDGS
except ImportError:
    try:
        from ddgs import DDGS
    except ImportError:
        DDGS = None

# Resilient Wikipedia import
try:
    import wikipedia
except ImportError:
    wikipedia = None


class AgenticRAG:
    """Lightweight Agentic RAG system with query routing, multi-source retrieval,

    verification, and synthesized answer generation.
    """

    def __init__(
        self,
        llm: Any,
        vector_db: Optional[Any] = None,
        sql_db: Optional[Any] = None,
        graph_db: Optional[Any] = None,
        wikipedia_db: Optional[Any] = None
    ):
        self.llm = llm
        self.vector_db = vector_db
        self.sql_db = sql_db
        self.graph_db = graph_db
        self.wikipedia_db = wikipedia_db

    def planner(self, query: str) -> List[str]:
        """Classify query intent to choose target retrieval sources."""
        q = (query or "").lower().strip()
        plan: List[str] = []

        # Structured data
        if any(word in q for word in [
            "count", "average", "maximum", "minimum",
            "price", "salary", "employee", "sales", "table", "sql"
        ]):
            plan.append("sql")

        # Relationships
        if any(word in q for word in [
            "connected", "relationship", "author",
            "citation", "dependency", "belongs", "graph"
        ]):
            plan.append("graph")

        # Wikipedia / Encyclopedic
        if any(word in q for word in [
            "who is", "history", "capital", "invented",
            "biography", "definition", "what is"
        ]):
            plan.append("wikipedia")

        # Internet / Real-time
        if any(word in q for word in [
            "latest", "today", "current", "news", "recent", "trends", "2024", "2025", "2026"
        ]):
            plan.append("web")

        # Semantic questions (default to vector if available or as default)
        if any(word in q for word in [
            "explain", "describe", "paper", "research",
            "what", "why", "how", "summary", "document"
        ]) or not plan:
            plan.append("vector")

        # Deduplicate preserving order
        seen = set()
        return [p for p in plan if not (p in seen or seen.add(p))]

    def vector_search(self, query: str) -> List[Dict[str, Any]]:
        """Search vector database."""
        if not self.vector_db:
            return []
        try:
            documents = self.vector_db.similarity_search(query, k=5)
            result = []
            for doc in documents:
                result.append({
                    "source": "vector",
                    "content": getattr(doc, "page_content", str(doc)),
                    "metadata": getattr(doc, "metadata", {})
                })
            return result
        except Exception as e:
            print(f"Vector search error: {e}")
            return []

    def sql_search(self, query: str) -> List[Dict[str, Any]]:
        """Search SQL database."""
        if not self.sql_db:
            return []

        q = query.lower()
        sql = ""
        if "employee" in q and "count" in q:
            sql = "SELECT COUNT(*) FROM employees;"
        elif "average salary" in q or ("average" in q and "salary" in q):
            sql = "SELECT AVG(salary) FROM employees;"
        elif "physics" in q:
            sql = "SELECT * FROM employees WHERE department='Physics';"

        if not sql:
            return []

        try:
            rows = self.sql_db.run(sql)
            return [{
                "source": "sql",
                "content": str(rows)
            }]
        except Exception as e:
            print(f"SQL search error: {e}")
            return []

    def graph_search(self, query: str) -> List[Dict[str, Any]]:
        """Search Graph database."""
        if not self.graph_db:
            return []

        q = query.lower()
        cypher = ""
        if "author" in q:
            cypher = "MATCH (a:Author)-[:WROTE]->(p:Paper) RETURN a.name, p.title LIMIT 5"
        elif "citation" in q:
            cypher = "MATCH (p1:Paper)-[:CITES]->(p2:Paper) RETURN p1.title, p2.title LIMIT 5"

        if not cypher:
            return []

        try:
            records = self.graph_db.query(cypher)
            return [{
                "source": "graph",
                "content": str(records)
            }]
        except Exception as e:
            print(f"Graph search error: {e}")
            return []

    def wikipedia_search(self, query: str) -> List[Dict[str, Any]]:
        """Search Wikipedia."""
        if wikipedia is None:
            return []
        clean_q = query.strip()
        if not clean_q:
            return []

        try:
            summary = wikipedia.summary(clean_q, sentences=3, auto_suggest=True)
            return [{
                "source": "wikipedia",
                "content": summary
            }]
        except getattr(wikipedia.exceptions, "DisambiguationError", Exception) as e:
            options = getattr(e, "options", [])
            if options:
                try:
                    summary = wikipedia.summary(options[0], sentences=3, auto_suggest=False)
                    return [{"source": "wikipedia", "content": summary}]
                except Exception:
                    pass
            return []
        except Exception:
            return []

    def web_search(self, query: str) -> List[Dict[str, Any]]:
        """Search the web using DuckDuckGo."""
        if DDGS is None:
            return []

        results = []
        try:
            with DDGS() as ddgs:
                search_results = ddgs.text(query, max_results=5)
                for r in search_results:
                    body = r.get("body", "").strip()
                    if body:
                        results.append({
                            "source": "web",
                            "content": body
                        })
        except Exception as e:
            print(f"Web search error: {e}")
        return results

    def rank_and_fuse(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate results."""
        return remove_duplicates(results)

    def verify(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out low-information or trivial content."""
        verified = []
        for r in results:
            content = r.get("content", "")
            if len(str(content).strip()) > 20:
                verified.append(r)
        return verified

    def generate_answer(self, query: str, context: List[Dict[str, Any]]) -> str:
        """Synthesize final response from context."""
        if not context:
            context_text = "No relevant context found."
        else:
            context_text = "\n\n".join(
                f"[{item.get('source', 'Unknown')}]: {item.get('content', '')}"
                for item in context
            )

        prompt = f"""You are a helpful and knowledgeable scientific assistant.

Context:
{context_text}

Question:
{query}

Answer the question clearly and accurately using the provided context. If the context does not contain enough information, explain what is known and mention what information is missing.
"""
        try:
            response = self.llm.invoke(prompt)
            return extract_llm_content(response)
        except Exception as e:
            return f"Answer generation failed: {str(e)}"

    def run(self, query: str) -> str:
        """Main execution pipeline with concurrent multi-source retrieval."""
        plan = self.planner(query)
        results = []

        source_dispatch = {
            "vector": self.vector_search,
            "sql": self.sql_search,
            "graph": self.graph_search,
            "wikipedia": self.wikipedia_search,
            "web": self.web_search,
        }

        # Concurrently execute retrieval sources
        tasks = [s for s in plan if s in source_dispatch]
        if len(tasks) == 1:
            results.extend(source_dispatch[tasks[0]](query))
        elif len(tasks) > 1:
            with ThreadPoolExecutor(max_workers=min(len(tasks), 4)) as executor:
                future_to_src = {
                    executor.submit(source_dispatch[src], query): src
                    for src in tasks
                }
                for future in as_completed(future_to_src):
                    try:
                        res = future.result()
                        if res:
                            results.extend(res)
                    except Exception as e:
                        print(f"Retrieval task error: {e}")

        # Deduplicate and verify
        results = self.rank_and_fuse(results)
        results = self.verify(results)

        return self.generate_answer(query, results)
