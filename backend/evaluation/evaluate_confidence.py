import sys
import os
import json

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from rag.retriever import retrieve_context


DATASET_PATH = os.path.join(
    os.path.dirname(__file__),
    "confidence_dataset.json"
)


def main():

    with open(
        DATASET_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        dataset = json.load(file)

    print("\nCONFIDENCE EVALUATION")
    print("=" * 70)

    for item in dataset:

        question = item["question"]
        expected = item["expected"]

        result = retrieve_context(
            question,
            k=4
        )

        score = result["score"]

        if score is None:
            predicted = "unknown"

        elif score >= 1.0:
            predicted = "relevant"

        else:
            predicted = "unknown"

        print(
            f"\nQuestion: {question}"
        )

        print(
            f"Expected: {expected}"
        )

        print(
            f"Score: {score}"
        )

        print(
            f"Predicted: {predicted}"
        )

        if expected == predicted:
            print("RESULT: PASS")
        else:
            print("RESULT: FAIL")


if __name__ == "__main__":
    main()