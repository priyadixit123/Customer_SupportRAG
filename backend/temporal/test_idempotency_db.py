
import sqlite3
import uuid
from pathlib import Path

DB_PATH = Path(__file__).with_name("temporal_results.db")

workflow_id = f"idempotency-test-{uuid.uuid4()}"
activity_id = "save_support_result-1"

conn = sqlite3.connect(DB_PATH)

try:
    columns = {
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(support_results)"
        ).fetchall()
    }

    if not {"workflow_id", "activity_id"} <= columns:
        raise RuntimeError(
            "Composite-key migration is missing. "
            "Run the database migration first."
        )

    insert_sql = """
        INSERT OR IGNORE INTO support_results
        (workflow_id, activity_id, answer, sources)
        VALUES (?, ?, ?, ?)
    """

    values = (
        workflow_id,
        activity_id,
        "Test answer",
        '["test-source"]',
    )

    conn.execute(insert_sql, values)
    conn.commit()

    conn.execute(insert_sql, values)
    conn.commit()

    count = conn.execute(
        """
        SELECT COUNT(*)
        FROM support_results
        WHERE workflow_id = ? AND activity_id = ?
        """,
        (workflow_id, activity_id),
    ).fetchone()[0]

    print("Rows for the same idempotency key:", count)
    print("PASS" if count == 1 else "FAIL")

finally:
    conn.execute(
        "DELETE FROM support_results WHERE workflow_id = ?",
        (workflow_id,),
    )
    conn.commit()
    conn.close()
