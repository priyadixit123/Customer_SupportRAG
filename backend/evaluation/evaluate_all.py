import os
import subprocess
import sys


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)


def run_test(name, script):
    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    script_path = os.path.join(
        BASE_DIR,
        "evaluation",
        script
    )

    result = subprocess.run(
        [sys.executable, script_path],
        cwd=BASE_DIR,
        text=True
    )

    if result.returncode != 0:
        print(f"\n❌ {name} FAILED")
        return False

    print(f"\n✅ {name} PASSED")
    return True


def main():

    results = []

    results.append(
        run_test(
            "GENERAL RETRIEVAL EVALUATION",
            "evaluate_retrieval.py"
        )
    )

    results.append(
        run_test(
            "NEAR-MISS EVALUATION",
            "evaluate_near_miss.py"
        )
    )

    results.append(
        run_test(
            "CONFIDENCE EVALUATION",
            "evaluate_confidence.py"
        )
    )

    print("\n" + "=" * 60)
    print("FINAL EVALUATION SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Evaluation suites passed: {passed}/{total}")

    if passed == total:
        print("STATUS: ✅ ALL TEST SUITES PASSED")
    else:
        print("STATUS: ⚠️ SOME TEST SUITES FAILED")


if __name__ == "__main__":
    main()