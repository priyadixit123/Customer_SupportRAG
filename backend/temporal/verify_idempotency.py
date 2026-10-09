import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "temporal_results.db"


def main():
    conn = sqlite3.connect(DB_PATH)

    try:
        rows = conn.execute("""
            SELECT workflow_id, COUNT(*) AS record_count
            FROM support_results
            GROUP BY workflow_id
        """).fetchall()

        if not rows:
            print("No saved results found.")
            return

        print("IDEMPOTENCY CHECK")
        print("-" * 40)

        duplicates_found = False

        for workflow_id, count in rows:
            status = "PASS" if count == 1 else "FAIL"
            print(f"{workflow_id}: {count} record(s) — {status}")

            if count != 1:
                duplicates_found = True

        if duplicates_found:
            print("\nFAIL: Duplicate records detected.")
        else:
            print("\nPASS: No duplicate records detected.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()