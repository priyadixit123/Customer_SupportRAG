from neo4j_client import Neo4jClient


client = Neo4jClient()


def create_graph():

    query = """
    // =========================
    // ANCILLARIES
    // =========================

    MERGE (seat:Ancillary {name: "Seat"})
    MERGE (baggage:Ancillary {name: "Baggage"})
    MERGE (meal:Ancillary {name: "Meal"})


    // =========================
    // SEAT OPTIONS
    // =========================

    MERGE (window:Option {name: "Window Seat"})
    MERGE (aisle:Option {name: "Aisle Seat"})
    MERGE (middle:Option {name: "Middle Seat"})
    MERGE (extraLegroom:Option {name: "Extra Legroom"})

    MERGE (seat)-[:HAS_OPTION]->(window)
    MERGE (seat)-[:HAS_OPTION]->(aisle)
    MERGE (seat)-[:HAS_OPTION]->(middle)
    MERGE (seat)-[:HAS_OPTION]->(extraLegroom)


    // =========================
    // BAGGAGE RULES
    // =========================

    MERGE (connectingFlight:Rule {
        name: "Connecting Flight"
    })

    MERGE (airlineSpecific:Rule {
        name: "Airline Specific"
    })

    MERGE (baggage)-[:HAS_RULE]->(connectingFlight)
    MERGE (baggage)-[:HAS_RULE]->(airlineSpecific)


    // =========================
    // MEAL OPTIONS
    // =========================

    MERGE (vegetarian:Option {
        name: "Vegetarian Meal"
    })

    MERGE (specialMeal:Option {
        name: "Special Meal"
    })

    MERGE (preOrder:Option {
        name: "Pre-Order Meal"
    })

    MERGE (meal)-[:HAS_OPTION]->(vegetarian)
    MERGE (meal)-[:HAS_OPTION]->(specialMeal)
    MERGE (meal)-[:HAS_OPTION]->(preOrder)


    // =========================
    // PROTECTION
    // =========================

    MERGE (cancellation:Protection {
        name: "Cancellation Protection"
    })

    MERGE (refundShield:Protection {
        name: "Refund Shield"
    })


    // =========================
    // REFUND SHIELD REASONS
    // =========================

    MERGE (medical:CoveredReason {
        name: "Medical Reason"
    })

    MERGE (travelDisruption:CoveredReason {
        name: "Travel Disruption"
    })

    MERGE (refundShield)-[:COVERS]->(medical)
    MERGE (refundShield)-[:COVERS]->(travelDisruption)


    RETURN count(*) AS total
    """


    with client.driver.session(
        database=client.database
    ) as session:

        result = session.run(query)

        record = result.single()

        print()
        print("=" * 60)
        print("HOLIDAYBREAKZ GRAPH CREATED")
        print("=" * 60)
        print("Result:", record["total"])


try:

    create_graph()

finally:

    client.close()