from .retriever import retrieve_context
from .graph_retriever import graph_retriever
from .query_router import detect_route


CONFIDENCE_THRESHOLD = 0.5


class FinalRetrievalPipeline:

    def search(self, query: str, k: int = 4):

        route = detect_route(query)

        print(f"RETRIEVAL ROUTE | {route}")

        context_parts = []
        scores = []
        sources = []

        # ----------------------------------------
        # RAG RETRIEVAL
        # ----------------------------------------

        if route in ["rag", "both"]:

            rag_result = retrieve_context(
                query,
                k=k
            )

            rag_context = rag_result.get(
                "context",
                ""
            )

            rag_score = rag_result.get(
                "score"
            )

            rag_sources = rag_result.get(
                "sources",
                []
            )

            print(
                "RAG SOURCES |",
                rag_sources
            )

            sources.extend(
                rag_sources
            )

            print(
                "PIPELINE SOURCES |",
                sources
            )

            if rag_context.strip():

                context_parts.append(
                    "KNOWLEDGE BASE:\n" +
                    rag_context
                )

            if rag_score is not None:

                scores.append(
                    rag_score
                )

                print(
                    f"RAG SCORE | {rag_score:.3f}"
                )

        # ----------------------------------------
        # GRAPH RAG
        # ----------------------------------------

        if route in ["graph", "both"]:

            try:

                graph_results = graph_retriever.search(
                    query
                )

                if graph_results:

                    graph_context = "\n".join(
                        graph_results
                    )

                    if graph_context.strip():

                        context_parts.append(
                            "GRAPH INFORMATION:\n" +
                            graph_context
                        )

                        print(
                            "GRAPH RETRIEVAL | SUCCESS"
                        )

            except Exception as e:

                print(
                    "GRAPH RETRIEVAL | FAILED"
                )

                print(
                    "GRAPH ERROR |",
                    repr(e)
                )

                print(
                    "GRAPH FALLBACK | Continuing with RAG"
                )

        # ----------------------------------------
        # FINAL CONTEXT
        # ----------------------------------------

        final_context = "\n\n---\n\n".join(
            context_parts
        )

        print(
            "FINAL SOURCES BEFORE CONFIDENCE |",
            sources
        )

        # ----------------------------------------
        # NO CONTEXT
        # ----------------------------------------

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

        # ----------------------------------------
        # GRAPH-ONLY ROUTE
        # ----------------------------------------

        if route == "graph":

            print(
                "RETRIEVAL CONFIDENCE | HIGH"
            )

            print(
                "FINAL SOURCES |",
                sources
            )

            return {
                "context": final_context,
                "confidence": "high",
                "route": route,
                "sources": sources
            }

        # ----------------------------------------
        # RAG CONFIDENCE
        # ----------------------------------------

        if scores:

            best_score = max(
                scores
            )

            if best_score >= CONFIDENCE_THRESHOLD:

                print(
                    "RETRIEVAL CONFIDENCE | HIGH"
                )

                print(
                    "FINAL SOURCES |",
                    sources
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

        # ----------------------------------------
        # DEFAULT LOW CONFIDENCE
        # ----------------------------------------

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


def retrieve_all(
    query: str,
    k: int = 4
):

    return retrieval_pipeline.search(
        query,
        k=k
    )