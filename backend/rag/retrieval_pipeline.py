import os
from .retriever import retrieve_context
from .graph_retriever import graph_retriever
from .query_router import detect_route

class FinalRetrievalPipeline:

    def get_calibrated_threshold(self) -> float:
        """Dynamically loads the calibrated threshold or falls back safely."""
        # Adjust path structure relative to this file's location to find CONFIDENCE_THRESHOLD
        threshold_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "CONFIDENCE_THRESHOLD"))
        if os.path.exists(threshold_path):
            try:
                with open(threshold_path, "r") as f:
                    return float(f.read().strip())
            except Exception as e:
                print(f"Error reading CONFIDENCE_THRESHOLD file: {e}")
        return 1.20  # Safe default baseline fallback verified by evaluation logs

    def search(self, query: str, k: int = 4):
        route = detect_route(query)
        confidence_threshold = self.get_calibrated_threshold()

        print(f"RETRIEVAL ROUTE | {route}")
        print(f"USING CALIBRATED THRESHOLD | {confidence_threshold:.3f}")

        context_parts = []
        sources = []
        scores = []
        rag_context_found = False
        graph_context_found = False

        # ----------------------------------------
        # RAG RETRIEVAL
        # ----------------------------------------
        if route in ["rag", "both"]:
            try:
                rag_result = retrieve_context(query, k=k)

                rag_context = rag_result.get("context", "") or ""
                rag_score = rag_result.get("score")
                rag_sources = rag_result.get("sources", []) or []

                print("RAG SOURCES |", rag_sources)

                if rag_context.strip():
                    context_parts.append(
                        "KNOWLEDGE BASE:\n" + rag_context
                    )
                    rag_context_found = True

                    for source in rag_sources:
                        if source not in sources:
                            sources.append(source)

                if rag_score is not None:
                    scores.append(rag_score)
                    print(f"RAG SCORE | {rag_score:.3f}")

            except Exception as e:
                print("RAG RETRIEVAL | FAILED")
                print("RAG ERROR |", repr(e))

        # ----------------------------------------
        # GRAPH RAG
        # ----------------------------------------
        if route in ["graph", "both"]:
            try:
                graph_results = graph_retriever.search(query)

                if graph_results:
                    graph_context = "\n".join(
                        str(item) for item in graph_results if item
                    )

                    if graph_context.strip():
                        context_parts.append(
                            "GRAPH INFORMATION:\n" + graph_context
                        )
                        graph_context_found = True
                        print("GRAPH RETRIEVAL | SUCCESS")
                    else:
                        print("GRAPH RETRIEVAL | EMPTY")
                else:
                    print("GRAPH RETRIEVAL | NO RESULTS")

            except Exception as e:
                print("GRAPH RETRIEVAL | FAILED")
                print("GRAPH ERROR |", repr(e))
                print("GRAPH FALLBACK | Continuing with RAG")

        # ----------------------------------------
        # FINAL CONTEXT ASSEMBLY & ROUTING
        # ----------------------------------------
        final_context = "\n\n---\n\n".join(context_parts)

        print("FINAL SOURCES |", sources)
        print("RAG CONTEXT FOUND |", rag_context_found)
        print("GRAPH CONTEXT FOUND |", graph_context_found)

        # 1. Immediate Escape: No usable context anywhere
        if not final_context.strip():
            print("RETRIEVAL CONFIDENCE | LOW")
            return {
                "context": "",
                "confidence": "low",
                "route": route,
                "sources": [],
            }

        # 2. Graph-only path
        if route == "graph":
            print("RETRIEVAL CONFIDENCE | HIGH")
            return {
                "context": final_context,
                "confidence": "high",
                "route": route,
                "sources": sources,
            }

        # 3. Handle scoring matches against your dynamic baseline
        if scores:
            best_score = max(scores)

            if best_score >= confidence_threshold:
                print("RETRIEVAL CONFIDENCE | HIGH")
                return {
                    "context": final_context,
                    "confidence": "high",
                    "route": route,
                    "sources": sources,
                }

            # If the route expects both datasets, don't drop structural graph knowledge
            if route == "both" and graph_context_found:
                print("RAG SCORE LOW | Keeping available graph context")
                return {
                    "context": final_context,
                    "confidence": "low",
                    "route": route,
                    "sources": sources,
                }

            print("RETRIEVAL CONFIDENCE | LOW")
            return {
                "context": "",
                "confidence": "low",
                "route": route,
                "sources": [],
            }

        # 4. Fallbacks for missing cross-encoder scoring values
        if graph_context_found:
            print("RETRIEVAL CONFIDENCE | LOW")
            return {
                "context": final_context,
                "confidence": "low",
                "route": route,
                "sources": sources,
            }

        print("RETRIEVAL CONFIDENCE | LOW")
        return {
            "context": "",
            "confidence": "low",
            "route": route,
            "sources": [],
        }


retrieval_pipeline = FinalRetrievalPipeline()

# =========================================================
# SYSTEM INTEGRATION ENTRYPOINT
# =========================================================
def retrieve_all(question: str, k: int = 4):
    """
    Cleaner interface mapped to AgentState nodes.
    Executes structural hybrid retrieval pipeline checks cleanly.
    """
    return retrieval_pipeline.search(query=question, k=k)
