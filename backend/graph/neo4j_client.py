import os

from dotenv import load_dotenv
from neo4j import GraphDatabase


load_dotenv()


class Neo4jClient:

    def __init__(self):

        self.uri = os.getenv("NEO4J_URI")
        self.username = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")

        self.database = os.getenv(
            "NEO4J_DATABASE",
            "neo4j"
        )

        if not self.uri:
            raise ValueError(
                "NEO4J_URI is missing from .env"
            )

        if not self.username:
            raise ValueError(
                "NEO4J_USERNAME is missing from .env"
            )

        if not self.password:
            raise ValueError(
                "NEO4J_PASSWORD is missing from .env"
            )

        self.driver = GraphDatabase.driver(
    self.uri.replace("neo4j+s://a79c9747.databases.neo4j.io", "neo4j+ssc://a79c9747.databases.neo4j.io"),
    auth=(
        self.username,
        self.password
    )
)
        

    def verify_connection(self):

        with self.driver.session(
            database=self.database
        ) as session:

            result = session.run(
                "RETURN 1 AS result"
            )

            record = result.single()

            return record["result"] == 1

    def close(self):

        self.driver.close()