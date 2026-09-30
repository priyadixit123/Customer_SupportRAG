from .retriever import retrieve_context
from .graph_retriever import graph_retriever
from .query_router import detect_route


CONFIDENCE_THRESHOLD = 1.0


class FinalRetrievalPipeline:

    def search(self, query: str, k: int = 4):

        route = detect_route(query)

        print(f"RETRIEVAL ROUTE | {route}")

        context_parts = []
        scores = []
        sources = []

        # NORMAL RAG
        if route in ["rag", "both"]:

            rag_result = retrieve_context(
                query,
                k=k
            )

            rag_context = rag_result["context"]
            rag_score = rag_result["score"]
            rag_sources = rag_result.get("sources", [])

            sources.extend(rag_sources)

            if rag_context.strip():
                context_parts.append(
                    "KNOWLEDGE BASE:\n" + rag_context
                )

            if rag_score is not None:
                scores.append(rag_score)

                print(
                    f"RAG SCORE | {rag_score:.3f}"
                )

        # NEO4J GRAPH RAG
        if route in ["graph", "both"]:

            graph_results = graph_retriever.search(query)

            if graph_results:

                graph_context = "\n".join(
                    graph_results
                )

                if graph_context.strip():
                    context_parts.append(
                        "GRAPH INFORMATION:\n"
                        + graph_context
                    )

        final_context = "\n\n---\n\n".join(
            context_parts
        )

        # Confidence decision
        if not final_context.strip():

            print(
                "RETRIEVAL CONFIDENCE | LOW"
            )

            return {
                "context": "",
                "confidence": "low",
                "route": route,
                "sources": []
            }

        # For Graph-only queries, graph evidence itself
        # is considered usable evidence.
        if route == "graph":

            print(
                "RETRIEVAL CONFIDENCE | HIGH"
            )

            return {
                "context": final_context,
                "confidence": "high",
                "route": route,
                "sources": sources
            }

        # For normal RAG, use CrossEncoder score.
        if scores:

            best_score = max(scores)

            if best_score >= CONFIDENCE_THRESHOLD:

                print(
                    "RETRIEVAL CONFIDENCE | HIGH"
                )

                return {
                    "context": final_context,
                    "confidence": "high",
                    "route": route,
                    "sources": sources
                }

            print(
                "RETRIEVAL CONFIDENCE | LOW"
            )

            return {
                "context": "",
                "confidence": "low",
                "route": route,
                "sources": []
            }

        print(
            "RETRIEVAL CONFIDENCE | LOW"
        )

        return {
            "context": "",
            "confidence": "low",
            "route": route,
            "sources": []
        }


retrieval_pipeline = FinalRetrievalPipeline()


def retrieve_all(query: str, k: int = 4):

    return retrieval_pipeline.search(
        query,
        k=k
    )