
from rag.retriever import retrieve_context

TEST_QUESTIONS = [
    "My booking is pending. How long should I wait?",
    "How long does booking confirmation take?",
    "When will I receive my refund?",
    "How long does a refund take after approval?",
]

for question in TEST_QUESTIONS:
    print("\n" + "=" * 70)
    print("QUESTION:", question)

    result = retrieve_context(question, k=4)

    print("\nSCORE:", result.get("score"))
    print("\nRETRIEVED SOURCES:")

    for source in result.get("sources", []):
        print(
            source.get("chunk_id"),
            "|",
            source.get("section"),
            "|",
            source.get("topic"),
        )

    print("\nCONTEXT:")
    print(result.get("context", "")[:1800])
