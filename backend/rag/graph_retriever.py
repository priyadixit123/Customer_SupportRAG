from graph.neo4j_client import Neo4jClient


# =========================================================
# Neo4j Client
# =========================================================

neo4j_client = Neo4jClient()


# =========================================================
# Graph Retriever
# =========================================================

class GraphRetriever:

    def search(self, query: str):

        query_lower = query.lower()

        # -------------------------------------------------
        # Entity detection
        # -------------------------------------------------

        if "refund shield" in query_lower:

            entity = "Refund Shield"
            entity_type = "Protection"

        elif "cancellation protection" in query_lower:

            entity = "Cancellation Protection"
            entity_type = "Protection"

        elif "baggage" in query_lower:

            entity = "Baggage"
            entity_type = "Ancillary"

        elif "seat" in query_lower:

            entity = "Seat"
            entity_type = "Ancillary"

        elif "meal" in query_lower:

            entity = "Meal"
            entity_type = "Ancillary"

        else:

            return []


        # -------------------------------------------------
        # Cypher query
        # -------------------------------------------------

        cypher = """
        MATCH (a)-[r]->(x)

        WHERE a.name = $entity
        AND $entity_type IN labels(a)

        RETURN
            a.name AS entity,
            labels(a)[0] AS entity_type,
            type(r) AS relationship,
            labels(x)[0] AS target_type,
            x.name AS target
        """


        # -------------------------------------------------
        # Execute query
        # -------------------------------------------------

        with neo4j_client.driver.session(
            database=neo4j_client.database
        ) as session:

            result = session.run(
                cypher,
                entity=entity,
                entity_type=entity_type
            )

            records = list(result)


        # -------------------------------------------------
        # Convert graph results to text
        # -------------------------------------------------

        graph_results = []

        for record in records:

            text = (
                f"{record['entity']} "
                f"{record['relationship']} "
                f"{record['target_type']}: "
                f"{record['target']}"
            )

            graph_results.append(text)


        return graph_results


# =========================================================
# Create Retriever
# =========================================================

graph_retriever = GraphRetriever()


# =========================================================
# Direct Test
# =========================================================

if __name__ == "__main__":

    query = input(
        "Enter question: "
    )

    results = graph_retriever.search(
        query
    )

    print()
    print("GRAPH RESULTS")
    print("=" * 60)

    if not results:

        print("No graph information found.")

    else:

        for result in results:

            print(result)