import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "temporal_results.db"


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python -m temporal.verify_one_workflow "
            "<workflow_id>"
        )
        raise SystemExit(2)

    workflow_id = sys.argv[1]

    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            """
            SELECT COUNT(*)
            FROM support_results
            WHERE workflow_id = ?
            """,
            (workflow_id,),
        ).fetchone()

    count = row[0]

    print("Workflow ID:", workflow_id)
    print("Saved records:", count)

    if count == 1:
        print("PASS: Exactly one record exists.")
    else:
        print("FAIL: Expected exactly one record.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()