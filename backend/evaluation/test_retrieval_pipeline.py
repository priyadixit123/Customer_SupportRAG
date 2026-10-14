from rag.retrieval_pipeline import retrieve_all

TEST_QUESTIONS = [
    "What seat options are available?",
    "How can I add baggage after booking?",
    "My booking is pending. How long should I wait?",
    "When will I receive my refund?",
    "How do I change my booking?",
    "Can I change my hotel room after checking in?",
    "What is the weather on Mars today?",
    "Write a Python program to sort a list.",
]

for question in TEST_QUESTIONS:
    print("\n" + "=" * 70)
    print("QUESTION:", question)

    try:
        result = retrieve_all(question, k=4)

        print("ROUTE:", result.get("route"))
        print("CONFIDENCE:", result.get("confidence"))
        print("SOURCES:", result.get("sources", []))
        print("CONTEXT:")
        print(result.get("context", "")[:1000])

    except Exception as exc:
        print("PIPELINE ERROR:", repr(exc))
