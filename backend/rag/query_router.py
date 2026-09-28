def detect_route(query: str) -> str:

    query_lower = query.lower()

    graph_keywords = [
        "connected",
        "relationship",
        "related",
        "linked",
        "graph",
        "covers",
        "covered by",
    ]

    graph_entities = [
        "seat",
        "baggage",
        "meal",
        "refund shield",
        "cancellation protection",
    ]

    has_graph_keyword = any(
        keyword in query_lower
        for keyword in graph_keywords
    )

    has_graph_entity = any(
        entity in query_lower
        for entity in graph_entities
    )

    # Explicit relationship question
    if has_graph_keyword and has_graph_entity:
        return "graph"

    # Entity question → use both KB and Graph
    if has_graph_entity:
        return "both"

    # General question → normal RAG
    return "rag"