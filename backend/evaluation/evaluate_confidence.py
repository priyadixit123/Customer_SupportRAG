
import sys
import os
import json
import csv

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from rag.retriever import retrieve_context

BASE_DIR = os.path.dirname(__file__)

DATASET_PATH = os.path.join(
    BASE_DIR,
    "confidence_dataset.json"
)

CSV_PATH = os.path.join(
    BASE_DIR,
    "confidence_results.csv"
)

THRESHOLDS = [-5.0, -2.0, -1.0, 0.0, 0.5, 0.96, 1.0, 2.0, 5.0]


def calculate_metrics(observations, threshold):
    tp = fp = tn = fn = 0

    for item in observations:
        expected_positive = item["expected"] == "relevant"
        score = item["score"]

        predicted_positive = (
            score is not None and score >= threshold
        )

        if predicted_positive and expected_positive:
            tp += 1
        elif predicted_positive and not expected_positive:
            fp += 1
        elif not predicted_positive and not expected_positive:
            tn += 1
        else:
            fn += 1

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )

    total = tp + fp + tn + fn
    accuracy = (tp + tn) / total if total else 0.0

    return {
        "threshold": threshold,
        "TP": tp,
        "FP": fp,
        "TN": tn,
        "FN": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
    }


def main():
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    observations = []

    print("\nCOLLECTING RETRIEVAL SCORES")
    print("=" * 70)

    for item in dataset:
        question = item["question"]
        expected = item["expected"]

        result = retrieve_context(question, k=4)
        score = result.get("score")

        observation = {
            "question": question,
            "expected": expected,
            "score": float(score) if score is not None else None,
            "sources": json.dumps(
                result.get("sources", []),
                ensure_ascii=False
            ),
        }

        observations.append(observation)

        print(
            f"Expected={expected:8} | "
            f"Score={str(score):>10} | {question}"
        )

    with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "question",
                "expected",
                "score",
                "sources",
            ],
        )
        writer.writeheader()
        writer.writerows(observations)

    print(f"\nDetailed results saved to: {CSV_PATH}")

    print("\nTHRESHOLD COMPARISON")
    print("=" * 80)
    print(
        f"{'Threshold':>10} {'TP':>4} {'FP':>4} {'TN':>4} "
        f"{'FN':>4} {'Precision':>10} {'Recall':>8} "
        f"{'F1':>8} {'Accuracy':>9}"
    )

    metrics = []

    for threshold in THRESHOLDS:
        result = calculate_metrics(observations, threshold)
        metrics.append(result)

        print(
            f"{threshold:10.2f} "
            f"{result['TP']:4d} {result['FP']:4d} "
            f"{result['TN']:4d} {result['FN']:4d} "
            f"{result['precision']:10.3f} "
            f"{result['recall']:8.3f} "
            f"{result['f1']:8.3f} "
            f"{result['accuracy']:9.3f}"
        )

    # Select the best tested threshold by F1.
    # In a production system, choose using a separate validation set.
    best = max(
        metrics,
        key=lambda item: (
            item["f1"],
            item["recall"],
            -item["threshold"],
        ),
    )

    print("\nBEST THRESHOLD ON THIS DATASET")
    print("-" * 70)
    print(f"Threshold: {best['threshold']:.2f}")
    print(f"Precision: {best['precision']:.3f}")
    print(f"Recall:    {best['recall']:.3f}")
    print(f"F1:        {best['f1']:.3f}")
    print(f"Accuracy:  {best['accuracy']:.3f}")

    print("\nNOTE")
    print("-" * 70)
    print("CrossEncoder scores are raw ranking scores, not probabilities.")
    print("The selected threshold is provisional, not production-validated.")
    print("Test on a separate validation set before deploying a confidence gate.")


if __name__ == "__main__":
    main()
