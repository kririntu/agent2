# retriever.py
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from typing import Any, Dict, List, Optional

# Safe import for DuckDuckGo
try:
    from duckduckgo_search import DDGS
except ImportError:
    try:
        from ddgs import DDGS
    except ImportError:
        DDGS = None

# Safe import for Wikipedia
try:
    import wikipedia
except ImportError:
    wikipedia = None

# Safe import for ArXiv
try:
    import arxiv
except ImportError:
    arxiv = None


class Retriever:
    """Multi-source retriever supporting Vector DB, ArXiv, Wikipedia, Web Search,

    SQL, and Graph databases.
    """

    def __init__(
        self,
        vector_db: Optional[Any] = None,
        sql_db: Optional[Any] = None,
        graph_db: Optional[Any] = None,
        arxiv_max_results: int = 5,
        web_max_results: int = 5
    ):
        self.vector_db = vector_db
        self.sql_db = sql_db
        self.graph_db = graph_db
        self.arxiv_max_results = arxiv_max_results
        self.web_max_results = web_max_results

        # Persistent arxiv client to avoid re-instantiation overhead
        self._arxiv_client = None
        if arxiv is not None:
            try:
                self._arxiv_client = arxiv.Client(
                    page_size=self.arxiv_max_results,
                    delay_seconds=1.0,
                    num_retries=3
                )
            except Exception:
                self._arxiv_client = None

    # ==========================================================
    # MAIN RETRIEVAL FUNCTION (CONCURRENT)
    # ==========================================================

    def retrieve(self, query: str, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Retrieve documents from all planned sources concurrently."""
        sources = plan.get("retrieve", [])
        if not sources:
            sources = ["arxiv"]

        results = []
        source_callables = {
            "vector": self.retrieve_vector,
            "arxiv": self.retrieve_arxiv,
            "wikipedia": self.retrieve_wikipedia,
            "web": self.retrieve_web,
            "sql": self.retrieve_sql,
            "graph": self.graph_search
        }

        # Filter only valid requested sources
        tasks_to_run = [s for s in sources if s in source_callables]

        if not tasks_to_run:
            return []

        # If only 1 source, execute synchronously to avoid thread overhead
        if len(tasks_to_run) == 1:
            source = tasks_to_run[0]
            print(f"  → Retrieving from: {source}")
            try:
                return source_callables[source](query)
            except Exception as e:
                print(f"Error in {source} retrieval: {e}")
                return []

        # Run multiple retrieval sources in parallel
        with ThreadPoolExecutor(max_workers=min(len(tasks_to_run), 4)) as executor:
            future_to_source = {
                executor.submit(source_callables[source], query): source
                for source in tasks_to_run
            }
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    res = future.result()
                    if res:
                        print(f"  ✓ {source}: retrieved {len(res)} items")
                        results.extend(res)
                    else:
                        print(f"  - {source}: 0 items found")
                except Exception as e:
                    print(f"  ✗ {source} retrieval error: {e}")

        return results

    # ==========================================================
    # VECTOR DATABASE
    # ==========================================================

    def retrieve_vector(self, query: str) -> List[Dict[str, Any]]:
        if not self.vector_db:
            return []

        results = []
        try:
            docs = self.vector_db.similarity_search(query, k=5)
            for doc in docs:
                meta = getattr(doc, "metadata", {}) or {}
                title = meta.get("title") or meta.get("source") or "Vector Document"
                results.append({
                    "source": "vector",
                    "title": title,
                    "content": getattr(doc, "page_content", str(doc)),
                    "url": meta.get("url", ""),
                    "metadata": meta
                })
        except Exception as e:
            print(f"Vector database retrieval error: {e}")

        return results

    # ==========================================================
    # ARXIV
    # ==========================================================

    def retrieve_arxiv(self, query: str) -> List[Dict[str, Any]]:
        if arxiv is None:
            print("ArXiv library is not installed.")
            return []

        # Clean query: strip characters that cause arXiv query parser syntax errors
        clean_q = re.sub(r"[^\w\s\-\.]", " ", query).strip()
        if not clean_q:
            return []

        results = []
        try:
            search = arxiv.Search(
                query=clean_q,
                max_results=self.arxiv_max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )

            client = self._arxiv_client or arxiv.Client(
                page_size=self.arxiv_max_results,
                delay_seconds=1.0,
                num_retries=2
            )

            for item in client.results(search):
                authors = [a.name for a in getattr(item, "authors", [])]
                results.append({
                    "source": "arxiv",
                    "title": item.title.strip(),
                    "content": item.summary.strip(),
                    "url": item.entry_id,
                    "pdf_url": getattr(item, "pdf_url", ""),
                    "authors": authors,
                    "published": str(getattr(item, "published", ""))
                })

        except Exception as e:
            print(f"arXiv retrieval error: {e}")

        return results

    # ==========================================================
    # WIKIPEDIA
    # ==========================================================

    def retrieve_wikipedia(self, query: str) -> List[Dict[str, Any]]:
        if wikipedia is None:
            return []

        clean_q = query.strip()
        if not clean_q:
            return []

        try:
            summary = wikipedia.summary(clean_q, sentences=4, auto_suggest=True)
            return [{
                "source": "wikipedia",
                "title": f"Wikipedia: {clean_q}",
                "content": summary.strip(),
                "url": f"https://en.wikipedia.org/wiki/{clean_q.replace(' ', '_')}"
            }]
        except getattr(wikipedia.exceptions, "DisambiguationError", Exception) as e:
            # Try the first suggested disambiguation option
            options = getattr(e, "options", [])
            if options:
                try:
                    first_opt = options[0]
                    summary = wikipedia.summary(first_opt, sentences=3, auto_suggest=False)
                    return [{
                        "source": "wikipedia",
                        "title": f"Wikipedia: {first_opt}",
                        "content": summary.strip(),
                        "url": f"https://en.wikipedia.org/wiki/{first_opt.replace(' ', '_')}"
                    }]
                except Exception:
                    pass
            return []
        except getattr(wikipedia.exceptions, "PageError", Exception):
            return []
        except Exception as e:
            print(f"Wikipedia retrieval error: {e}")
            return []

    # ==========================================================
    # WEB SEARCH
    # ==========================================================

    def retrieve_web(self, query: str) -> List[Dict[str, Any]]:
        if DDGS is None:
            print("DuckDuckGo search (DDGS) is not available.")
            return []

        results = []
        try:
            with DDGS() as ddgs:
                search_results = ddgs.text(query, max_results=self.web_max_results)
                for r in search_results:
                    body = r.get("body", "").strip()
                    title = r.get("title", "").strip()
                    url = r.get("href", "").strip()
                    if body:
                        results.append({
                            "source": "web",
                            "title": title or "Web Result",
                            "content": body,
                            "url": url
                        })
        except Exception as e:
            print(f"Web retrieval error: {e}")

        return results

    # ==========================================================
    # SQL DATABASE
    # ==========================================================

    def retrieve_sql(self, query: str) -> List[Dict[str, Any]]:
        if not self.sql_db:
            return []

        q = query.lower()
        sql = ""

        if "employee" in q or "count" in q:
            sql = "SELECT COUNT(*) FROM employees;"
        elif "average" in q and "salary" in q:
            sql = "SELECT AVG(salary) FROM employees;"
        elif "physics" in q:
            sql = "SELECT * FROM employees WHERE department = 'Physics';"

        if not sql:
            return []

        try:
            rows = self.sql_db.run(sql)
            return [{
                "source": "sql",
                "title": f"SQL Query: {sql.strip()}",
                "content": str(rows),
                "url": ""
            }]
        except Exception as e:
            print(f"SQL retrieval error: {e}")
            return []

    # ==========================================================
    # GRAPH DATABASE
    # ==========================================================

    def graph_search(self, query: str) -> List[Dict[str, Any]]:
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
                "title": f"Graph Query: {cypher}",
                "content": str(records),
                "url": ""
            }]
        except Exception as e:
            print(f"Graph retrieval error: {e}")
            return []
