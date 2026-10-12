
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("temporal_results.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)

    try:
        conn.execute("BEGIN IMMEDIATE")

        columns = {
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(support_results)"
            ).fetchall()
        }

        if not columns:
            raise RuntimeError(
                "support_results table was not found."
            )

        if "activity_id" in columns:
            print("Migration already applied; no changes needed.")
            conn.rollback()
            return

        old_count = conn.execute(
            "SELECT COUNT(*) FROM support_results"
        ).fetchone()[0]

        conn.execute(
            "ALTER TABLE support_results "
            "RENAME TO support_results_old"
        )

        conn.execute("""
            CREATE TABLE support_results (
                workflow_id TEXT NOT NULL,
                activity_id TEXT NOT NULL,
                answer TEXT NOT NULL,
                sources TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (workflow_id, activity_id)
            )
        """)

        conn.execute("""
            INSERT INTO support_results
                (workflow_id, activity_id, answer, sources, created_at)
            SELECT
                workflow_id, 'legacy', answer, sources, created_at
            FROM support_results_old
        """)

        new_count = conn.execute(
            "SELECT COUNT(*) FROM support_results"
        ).fetchone()[0]

        if old_count != new_count:
            raise RuntimeError(
                f"Row count mismatch: {old_count} old, {new_count} new."
            )

        conn.execute("DROP TABLE support_results_old")
        conn.commit()

        print("Migration successful.")
        print(f"Preserved records: {new_count}")
        print("New primary key: (workflow_id, activity_id)")

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
