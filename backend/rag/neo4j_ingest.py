import os
from pathlib import Path

from neo4j import GraphDatabase
from dotenv import load_dotenv


# =========================================================
# Load Environment Variables
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)


# =========================================================
# Neo4j Configuration
# =========================================================

NEO4J_URI = os.getenv(
    "NEO4J_URI"
)

NEO4J_USERNAME = os.getenv(
    "NEO4J_USERNAME"
)

NEO4J_PASSWORD = os.getenv(
    "NEO4J_PASSWORD"
)


# =========================================================
# Validate Configuration
# =========================================================

if not NEO4J_URI:
    raise ValueError(
        "NEO4J_URI is missing from .env"
    )

if not NEO4J_USERNAME:
    raise ValueError(
        "NEO4J_USERNAME is missing from .env"
    )

if not NEO4J_PASSWORD:
    raise ValueError(
        "NEO4J_PASSWORD is missing from .env"
    )


# =========================================================
# Create Neo4j Driver
# =========================================================

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(
        NEO4J_USERNAME,
        NEO4J_PASSWORD
    )
)


# =========================================================
# Test Connection
# =========================================================

def test_connection():

    with driver.session() as session:

        result = session.run(
            "RETURN 'Neo4j connection successful' AS message"
        )

        record = result.single()

        print(record["message"])


# =========================================================
# Clear Existing Graph
# =========================================================

def clear_database():

    with driver.session() as session:

        session.run(
            """
            MATCH (n)
            DETACH DELETE n
            """
        )

    print("Existing graph deleted.")


# =========================================================
# Create Ancillary
# =========================================================

def create_ancillary(
    name,
    description
):

    with driver.session() as session:

        session.run(
            """
            MERGE (a:Ancillary {
                name: $name
            })

            SET a.description = $description
            """,
            name=name,
            description=description
        )


# =========================================================
# Create Rule
# =========================================================

def create_rule(
    ancillary_name,
    rule
):

    with driver.session() as session:

        session.run(
            """
            MERGE (a:Ancillary {
                name: $ancillary_name
            })

            MERGE (r:Rule {
                text: $rule
            })

            MERGE (a)-[:HAS_RULE]->(r)
            """,
            ancillary_name=ancillary_name,
            rule=rule
        )


# =========================================================
# Create Action
# =========================================================

def create_action(
    ancillary_name,
    action
):

    with driver.session() as session:

        session.run(
            """
            MERGE (a:Ancillary {
                name: $ancillary_name
            })

            MERGE (act:Action {
                name: $action
            })

            MERGE (a)-[:HAS_ACTION]->(act)
            """,
            ancillary_name=ancillary_name,
            action=action
        )


# =========================================================
# Create Price
# =========================================================

def create_price(
    ancillary_name,
    price
):

    with driver.session() as session:

        session.run(
            """
            MERGE (a:Ancillary {
                name: $ancillary_name
            })

            MERGE (p:Price {
                text: $price
            })

            MERGE (a)-[:HAS_PRICE]->(p)
            """,
            ancillary_name=ancillary_name,
            price=price
        )


# =========================================================
# Load HolidayBreakz Knowledge
# =========================================================

def load_holidaybreakz_graph():

    print()
    print("=" * 60)
    print("Loading HolidayBreakz Graph")
    print("=" * 60)


    # -----------------------------------------------------
    # SEAT
    # -----------------------------------------------------

    create_ancillary(
        "Seat",
        "Seat selection ancillary"
    )

    create_rule(
        "Seat",
        "Seat selection does not guarantee a specific seat."
    )

    create_rule(
        "Seat",
        "Seat prices vary by market."
    )

    create_action(
        "Seat",
        "Select seat while booking"
    )

    create_action(
        "Seat",
        "Select seat after booking"
    )

    create_action(
        "Seat",
        "Change or remove seat"
    )

    create_price(
        "Seat",
        "Market-wise seat pricing"
    )


    # -----------------------------------------------------
    # BAGGAGE
    # -----------------------------------------------------

    create_ancillary(
        "Baggage",
        "Baggage allowance and excess baggage ancillary"
    )

    create_rule(
        "Baggage",
        "Baggage allowance is airline and segment specific."
    )

    create_rule(
        "Baggage",
        "Baggage does not automatically apply to every booking."
    )

    create_action(
        "Baggage",
        "Add baggage while booking"
    )

    create_action(
        "Baggage",
        "Add baggage after booking"
    )

    create_action(
        "Baggage",
        "Remove baggage"
    )

    create_price(
        "Baggage",
        "Market-wise baggage pricing"
    )


    # -----------------------------------------------------
    # MEAL
    # -----------------------------------------------------

    create_ancillary(
        "Meal",
        "Meal selection and pre-order ancillary"
    )

    create_rule(
        "Meal",
        "Meal requests are not automatically guaranteed."
    )

    create_rule(
        "Meal",
        "Meal availability depends on the airline."
    )

    create_action(
        "Meal",
        "Select meal while booking"
    )

    create_action(
        "Meal",
        "Add meal after booking"
    )

    create_action(
        "Meal",
        "Change or remove meal"
    )

    create_price(
        "Meal",
        "Market-wise meal pricing"
    )


    # -----------------------------------------------------
    # CANCELLATION PROTECTION
    # -----------------------------------------------------

    create_ancillary(
        "Cancellation Protection",
        "Protection product related to cancellation"
    )

    create_rule(
        "Cancellation Protection",
        "Coverage depends on the applicable protection terms."
    )

    create_action(
        "Cancellation Protection",
        "Buy during booking"
    )

    create_action(
        "Cancellation Protection",
        "Add after booking"
    )

    create_action(
        "Cancellation Protection",
        "Remove protection"
    )

    create_action(
        "Cancellation Protection",
        "Use protection"
    )


    # -----------------------------------------------------
    # REFUND SHIELD
    # -----------------------------------------------------

    create_ancillary(
        "Refund Shield",
        "Protection product related to refund requests"
    )

    create_rule(
        "Refund Shield",
        "Covered reasons depend on the applicable policy."
    )

    create_action(
        "Refund Shield",
        "Add Refund Shield"
    )

    create_action(
        "Refund Shield",
        "Add after booking"
    )

    create_action(
        "Refund Shield",
        "Remove Refund Shield"
    )

    create_action(
        "Refund Shield",
        "Request Refund Shield refund"
    )

    create_price(
        "Refund Shield",
        "Refund Shield pricing"
    )


    print()
    print("HolidayBreakz graph loaded successfully.")


# =========================================================
# Main
# =========================================================

if __name__ == "__main__":

    try:

        test_connection()

        clear_database()

        load_holidaybreakz_graph()

    finally:

        driver.close()