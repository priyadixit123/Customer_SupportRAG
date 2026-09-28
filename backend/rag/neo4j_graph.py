from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))

from neo4j_connection import driver


# =========================================================
# Create Ancillary
# =========================================================

def create_ancillary(
    session,
    name,
    description
):

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
    session,
    ancillary_name,
    rule
):

    session.run(
        """
        MATCH (a:Ancillary {
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
    session,
    ancillary_name,
    action
):

    session.run(
        """
        MATCH (a:Ancillary {
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
    session,
    ancillary_name,
    price
):

    session.run(
        """
        MATCH (a:Ancillary {
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
# Build HolidayBreakz Graph
# =========================================================

def build_graph():

    with driver.session() as session:

        # =================================================
        # SEAT
        # =================================================

        create_ancillary(
            session,
            "Seat",
            "Seat selection ancillary"
        )

        create_rule(
            session,
            "Seat",
            "Seat selection does not guarantee a specific seat."
        )

        create_rule(
            session,
            "Seat",
            "Seat prices vary by market."
        )

        create_action(
            session,
            "Seat",
            "Select seat while booking"
        )

        create_action(
            session,
            "Seat",
            "Select seat after booking"
        )

        create_action(
            session,
            "Seat",
            "Change or remove seat"
        )

        create_price(
            session,
            "Seat",
            "Market-wise seat pricing"
        )


        # =================================================
        # BAGGAGE
        # =================================================

        create_ancillary(
            session,
            "Baggage",
            "Baggage allowance and excess baggage ancillary"
        )

        create_rule(
            session,
            "Baggage",
            "Baggage allowance is airline and segment specific."
        )

        create_rule(
            session,
            "Baggage",
            "Baggage does not automatically apply to every booking."
        )

        create_action(
            session,
            "Baggage",
            "Add baggage while booking"
        )

        create_action(
            session,
            "Baggage",
            "Add baggage after booking"
        )

        create_action(
            session,
            "Baggage",
            "Remove baggage"
        )

        create_price(
            session,
            "Baggage",
            "Market-wise baggage pricing"
        )


        # =================================================
        # MEAL
        # =================================================

        create_ancillary(
            session,
            "Meal",
            "Meal selection and pre-order ancillary"
        )

        create_rule(
            session,
            "Meal",
            "Meal requests are not automatically guaranteed."
        )

        create_rule(
            session,
            "Meal",
            "Meal availability depends on the airline."
        )

        create_action(
            session,
            "Meal",
            "Select meal while booking"
        )

        create_action(
            session,
            "Meal",
            "Add meal after booking"
        )

        create_action(
            session,
            "Meal",
            "Change or remove meal"
        )

        create_price(
            session,
            "Meal",
            "Market-wise meal pricing"
        )


        # =================================================
        # CANCELLATION PROTECTION
        # =================================================

        create_ancillary(
            session,
            "Cancellation Protection",
            "Protection product related to cancellation"
        )

        create_rule(
            session,
            "Cancellation Protection",
            "Coverage depends on the applicable protection terms."
        )

        create_action(
            session,
            "Cancellation Protection",
            "Buy during booking"
        )

        create_action(
            session,
            "Cancellation Protection",
            "Add after booking"
        )

        create_action(
            session,
            "Cancellation Protection",
            "Remove protection"
        )

        create_action(
            session,
            "Cancellation Protection",
            "Use protection"
        )


        # =================================================
        # REFUND SHIELD
        # =================================================

        create_ancillary(
            session,
            "Refund Shield",
            "Protection product related to refund requests"
        )

        create_rule(
            session,
            "Refund Shield",
            "Covered reasons depend on the applicable policy."
        )

        create_action(
            session,
            "Refund Shield",
            "Add Refund Shield"
        )

        create_action(
            session,
            "Refund Shield",
            "Add after booking"
        )

        create_action(
            session,
            "Refund Shield",
            "Remove Refund Shield"
        )

        create_action(
            session,
            "Refund Shield",
            "Request Refund Shield refund"
        )

        create_price(
            session,
            "Refund Shield",
            "Refund Shield pricing"
        )


        print("HolidayBreakz graph created successfully.")


# =========================================================
# Main
# =========================================================

if __name__ == "__main__":

    try:

        build_graph()

    except Exception as e:

        print("Graph creation failed.")
        print(e)

    finally:

        driver.close()