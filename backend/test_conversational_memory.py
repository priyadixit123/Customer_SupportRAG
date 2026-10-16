
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver


def test_agent_remembers_previous_conversation(
    tmp_path,
    monkeypatch,
):
    print("DEBUG: Importing agent...", flush=True)
    import agent
    print("DEBUG: Agent imported.", flush=True)

    # Mock retrieval so the test does not depend on Chroma,
    # BM25, reranking, Neo4j, or the external knowledge base.
    def fake_retrieve_all(question, k=4):
        return {
            "context": (
                "HolidayBreakz customer support can help "
                "with booking-related questions."
            ),
            "confidence": "high",
            "route": "llm",
            "sources": ["test_knowledge_base"],
        }

    monkeypatch.setattr(
        agent,
        "retrieve_all",
        fake_retrieve_all,
    )

    # Mock the LLM to make the test deterministic and free.
    class FakeResponse:
        def __init__(self, content):
            self.content = content

    class FakeLLM:
        def invoke(self, prompt):
            prompt_text = str(prompt)
            prompt_upper = prompt_text.upper()

            print(
                "DEBUG: FakeLLM invoked.",
                flush=True,
            )

            # Simulate the factuality auditor.
            if "STRICT FACTUAL AUDITOR" in prompt_upper:
                if "HB12345" in prompt_text:
                    return FakeResponse("FAITHFUL")

                return FakeResponse("UNFAITHFUL")

            # Simulate the follow-up response using history.
            if "WHAT WAS MY BOOKING REFERENCE" in prompt_upper:
                if "HB12345" in prompt_text:
                    return FakeResponse(
                        "Your booking reference is HB12345."
                    )

                return FakeResponse(
                    agent.FALLBACK_MESSAGE
                )

            # Simulate the first turn.
            if "HB12345" in prompt_text:
                return FakeResponse(
                    "I will remember your booking reference "
                    "HB12345 during this conversation."
                )

            return FakeResponse(agent.FALLBACK_MESSAGE)

    monkeypatch.setattr(agent, "llm", FakeLLM())

    # Use a temporary SQLite database.
    db_path = tmp_path / "conversation_memory_test.db"

    connection = sqlite3.connect(
        str(db_path),
        check_same_thread=False,
    )

    try:
        checkpointer = SqliteSaver(connection)

        test_graph = agent.builder.compile(
            checkpointer=checkpointer,
        )

        config = {
            "configurable": {
                "thread_id": "conversation-memory-test",
            }
        }

        # ---------------------------------------------
        # Turn 1: Share a booking reference
        # ---------------------------------------------
        first_input = {
            "user_question": (
                "My booking reference is HB12345. "
                "Please remember it."
            ),
            "topic": "",
            "context": "",
            "confidence": "low",
            "route": "",
            "sources": [],
            "answer": "",
            "error": "",
        }

        print(
            "DEBUG: Starting first graph invocation...",
            flush=True,
        )

        first_result = test_graph.invoke(
            first_input,
            config=config,
        )

        print(
            "DEBUG: First graph invocation completed.",
            flush=True,
        )
        print(
            "DEBUG: First result:",
            first_result,
            flush=True,
        )

        assert first_result.get("answer"), (
            "The first turn returned no answer."
        )

        first_state = test_graph.get_state(config)

        saved_history = first_state.values.get(
            "conversation_history",
            "",
        )

        assert "HB12345" in str(saved_history), (
            "The first turn was not saved in conversation history."
        )

        print(
            "PASS: First turn saved to conversation history.",
            flush=True,
        )

        # ---------------------------------------------
        # Turn 2: Ask about the earlier reference
        # ---------------------------------------------
        second_input = {
            "user_question": "What was my booking reference?",
            "topic": "",
            "context": "",
            "confidence": "low",
            "route": "",
            "sources": [],
            "answer": "",
            "error": "",
        }

        # Reuse the same thread ID so LangGraph can restore
        # the previous checkpoint.
        print(
            "DEBUG: Starting second graph invocation...",
            flush=True,
        )

        second_result = test_graph.invoke(
            second_input,
            config=config,
        )

        print(
            "DEBUG: Second graph invocation completed.",
            flush=True,
        )
        print(
            "DEBUG: Second result:",
            second_result,
            flush=True,
        )

        answer = str(second_result.get("answer", ""))

        print("Follow-up answer:", answer, flush=True)

        assert "HB12345" in answer, (
            "The agent did not recall the previous booking reference."
        )

        final_state = test_graph.get_state(config)

        final_history = final_state.values.get(
            "conversation_history",
            "",
        )

        assert "HB12345" in str(final_history), (
            "The conversation history lost the booking reference."
        )

        assert (
            "What was my booking reference?" in str(final_history)
        ), (
            "The follow-up turn was not saved to conversation history."
        )

        print(
            "PASS: Agent recalled the previous booking reference.",
            flush=True,
        )
        print(
            "PASS: Follow-up turn was saved to history.",
            flush=True,
        )

    finally:
        connection.close()
