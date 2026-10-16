
import sqlite3
import uuid
from pathlib import Path

import pytest
from langgraph.checkpoint.sqlite import SqliteSaver


# Store checkpoints in the backend folder.
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "holidaybreakz_checkpoints.db"


def test_persistence_survives_connection_restart():
    """
    Verify that:
    1. The first conversation turn creates a checkpoint.
    2. The checkpoint survives closing and reopening SQLite.
    3. A follow-up turn updates the checkpoint.
    """

    # Import the application only when the test runs.
    # This helps avoid importing heavy AI models during pytest collection.
    from agent import builder

    # Use a unique ID to avoid interference from previous test runs.
    thread_id = f"persistence-test-{uuid.uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}

    conn = None
    new_conn = None

    try:
        # -----------------------------------------
        # STEP 1: Open SQLite and compile the graph
        # -----------------------------------------
        conn = sqlite3.connect(
            str(DB_PATH),
            check_same_thread=False,
        )

        memory = SqliteSaver(conn)
        graph = builder.compile(checkpointer=memory)

        # -----------------------------------------
        # STEP 2: Run the first conversation turn
        # -----------------------------------------
        initial_input = {
            "user_question": "What seat options are available?",
            "conversation_history": "",
            "topic": "seat_selection",
            "context": "",
            "confidence": "",
            "route": "",
            "sources": [],
            "answer": "",
            "error": "",
        }

        output_turn_1 = graph.invoke(
            initial_input,
            config=config,
        )

        answer_1 = output_turn_1.get("answer", "")

        assert answer_1, "First turn returned no answer."

        print("\nFirst answer:", answer_1)

        # -----------------------------------------
        # STEP 3: Verify the checkpoint was saved
        # -----------------------------------------
        saved_state = graph.get_state(config)

        assert saved_state.config, (
            "No checkpoint saved after the first turn."
        )

        assert (
            saved_state.values.get("user_question")
            == initial_input["user_question"]
        ), "Saved checkpoint contains an unexpected question."

        print("Checkpoint saved successfully.")

        # -----------------------------------------
        # STEP 4: Close the original connection
        # -----------------------------------------
        conn.close()
        conn = None

        print("SQLite connection closed.")

        # -----------------------------------------
        # STEP 5: Reopen SQLite and rebuild graph
        # -----------------------------------------
        new_conn = sqlite3.connect(
            str(DB_PATH),
            check_same_thread=False,
        )

        new_memory = SqliteSaver(new_conn)
        restarted_graph = builder.compile(
            checkpointer=new_memory
        )

        # -----------------------------------------
        # STEP 6: Restore the previous checkpoint
        # -----------------------------------------
        restored_state = restarted_graph.get_state(config)

        assert restored_state.config, (
            "No checkpoint restored after reopening SQLite."
        )

        restored_question = restored_state.values.get(
            "user_question"
        )

        assert restored_question == initial_input["user_question"], (
            "Restored checkpoint does not contain the first question."
        )

        print("Restored previous question:", restored_question)
        print("Checkpoint restored successfully.")

        # -----------------------------------------
        # STEP 7: Run a follow-up conversation turn
        # -----------------------------------------
        follow_up_input = {
            "user_question": (
                "Can I choose my seat after I book my ticket?"
            ),
            "conversation_history": "",
            "topic": "seat_selection",
            "context": "",
            "confidence": "",
            "route": "",
            "sources": [],
            "answer": "",
            "error": "",
        }

        output_turn_2 = restarted_graph.invoke(
            follow_up_input,
            config=config,
        )

        answer_2 = output_turn_2.get("answer", "")

        assert answer_2, "Follow-up turn returned no answer."

        print("\nFollow-up answer:", answer_2)

        # -----------------------------------------
        # STEP 8: Verify the checkpoint was updated
        # -----------------------------------------
        final_state = restarted_graph.get_state(config)

        assert (
            final_state.values.get("user_question")
            == follow_up_input["user_question"]
        ), "Checkpoint was not updated after the follow-up turn."

        print("\nPASS: Checkpoint persisted across connection restart.")
        print("PASS: Checkpoint updated after the follow-up turn.")

    finally:
        # Always close connections, including when an assertion fails.
        if conn is not None:
            conn.close()

        if new_conn is not None:
            new_conn.close()
