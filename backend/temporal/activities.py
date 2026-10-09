import json
import os
import sqlite3
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("holidaybreakz.temporal.activities")

from temporalio import activity


DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "temporal_results.db"
)

def log_activity_event(event: str) -> None:
    info = activity.info()

    logger.info(
        "%s | workflow_id=%s | activity_id=%s | "
        "activity_type=%s | attempt=%s",
        event,
        info.workflow_id,
        info.activity_id,
        info.activity_type,
        info.attempt,
    )


def init_database():

    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS support_results (
            workflow_id TEXT PRIMARY KEY,
            answer TEXT NOT NULL,
            sources TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


@activity.defn
async def retrieve_support_context(
    question: str,
    session_id: str
) -> dict:

    from agent import ask_agent

    result = ask_agent(
        question,
        session_id
    )

    return {
        "answer": result.get("answer", ""),
        "sources": result.get("sources", [])
    }


@activity.defn
async def generate_support_answer(
    context: dict
) -> dict:

    return {
        "answer": context.get("answer", ""),
        "sources": context.get("sources", [])
    }




@activity.defn
async def save_support_result(result: dict) -> dict:
    log_activity_event("save_started")

    init_database()
    workflow_id = activity.info().workflow_id

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO support_results
            (workflow_id, answer, sources)
            VALUES (?, ?, ?)
            """,
            (
                workflow_id,
                result.get("answer", ""),
                json.dumps(result.get("sources", [])),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    log_activity_event("save_committed")
    logger.info("Result stored | workflow_id=%s", workflow_id)

    log_activity_event("save_completed")

    return {
        "answer": result.get("answer", ""),
        "sources": result.get("sources", []),
    }

   

    

    