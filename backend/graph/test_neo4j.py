
from neo4j_client import Neo4jClient

client = Neo4jClient()


try:

    connected = client.verify_connection()

    if connected:

        print()
        print("=" * 50)
        print("Neo4j Aura connection successful!")
        print("=" * 50)

    else:

        print()
        print("Neo4j connection failed.")


finally:

    client.close()