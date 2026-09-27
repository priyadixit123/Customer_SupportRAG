import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase


# =========================================================
# Load environment variables
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]

ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE)




# =========================================================
# Neo4j Configuration
# =========================================================

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv(
    "NEO4J_DATABASE",
    "neo4j"
)

if not NEO4J_URI:
    raise ValueError("NEO4J_URI is missing")

if not NEO4J_USERNAME:
    raise ValueError("NEO4J_USERNAME is missing")

if not NEO4J_PASSWORD:
    raise ValueError("NEO4J_PASSWORD is missing")


# =========================================================
# Neo4j Driver
# =========================================================

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(
        NEO4J_USERNAME,
        NEO4J_PASSWORD
    )
)


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
        # Query Neo4j
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


        with driver.session(
            database=NEO4J_DATABASE
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
# Test
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