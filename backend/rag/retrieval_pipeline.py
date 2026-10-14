
from .retriever import retrieve_context
from .graph_retriever import graph_retriever
from .query_router import detect_route


CONFIDENCE_THRESHOLD = 0.5


class FinalRetrievalPipeline:

    def search(self, query: str, k: int = 4):
        route = detect_route(query)

        print(f"RETRIEVAL ROUTE | {route}")

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
                        str(item)
                        for item in graph_results
                        if item
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
        # FINAL CONTEXT
        # ----------------------------------------
        final_context = "\n\n---\n\n".join(context_parts)

        print("FINAL SOURCES |", sources)
        print("RAG CONTEXT FOUND |", rag_context_found)
        print("GRAPH CONTEXT FOUND |", graph_context_found)

        # No usable context from either retriever
        if not final_context.strip():
            print("RETRIEVAL CONFIDENCE | LOW")

            return {
                "context": "",
                "confidence": "low",
                "route": route,
                "sources": [],
            }

        # Graph-only retrieval: useful context is available,
        # but this does not independently prove answer correctness.
        if route == "graph":
            print("RETRIEVAL CONFIDENCE | HIGH")

            return {
                "context": final_context,
                "confidence": "high",
                "route": route,
                "sources": sources,
            }

        # RAG score check
        if scores:
            best_score = max(scores)

            if best_score >= CONFIDENCE_THRESHOLD:
                print("RETRIEVAL CONFIDENCE | HIGH")

                return {
                    "context": final_context,
                    "confidence": "high",
                    "route": route,
                    "sources": sources,
                }

            # IMPORTANT:
            # If the route is "both", do not discard valid graph
            # information just because the RAG score is low.
            if route == "both" and graph_context_found:
                print(
                    "RAG SCORE LOW | Keeping available graph context"
                )

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

        # No RAG score available, but graph information may still exist.
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


def retrieve_all(query: str, k: int = 4):
    return retrieval_pipeline.search(query, k=k)
