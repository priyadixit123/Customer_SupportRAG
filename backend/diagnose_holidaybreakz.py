
import importlib.util
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

print("=" * 60)
print("HOLIDAYBREAKZ ROOT-CAUSE DIAGNOSTIC")
print("=" * 60)


def check(label, function):
    print(f"\n--- {label} ---", flush=True)
    started = time.perf_counter()

    try:
        result = function()
        elapsed = time.perf_counter() - started
        print(f"PASS ({elapsed:.2f}s)")
        if result is not None:
            print(result)
        return True
    except Exception as exc:
        elapsed = time.perf_counter() - started
        print(f"FAIL ({elapsed:.2f}s)")
        print(f"{type(exc).__name__}: {exc}")
        traceback.print_exc()
        return False


def inspect_files():
    files = [
        "agent.py",
        "test_conversational_memory.py",
        "test_persistence.py",
        "rag/reranker.py",
        "rag/retrieval_pipeline.py",
    ]

    for name in files:
        print(f"{name}: {('FOUND' if (ROOT / name).exists() else 'MISSING')}")

    return "File inspection complete"


def inspect_agent():
    import agent

    print("Agent file:", agent.__file__)
    print("History node registered:",
          "save_history" in agent.builder.nodes)
    print("Graph nodes:", list(agent.builder.nodes.keys()))

    print("Graph edges:")
    for edge in agent.builder.edges:
        print(f"  {edge[0]} -> {edge[1]}")

    return "Agent imported and graph inspected"


def test_history_node():
    import agent

    state = {
        "user_question": "My booking reference is HB12345.",
        "answer": "I will remember HB12345.",
        "conversation_history": "",
    }

    result = agent.save_conversation_history_node(state)

    print("Node output:", repr(result))

    history = result.get("conversation_history", "")

    assert "HB12345" in history, (
        "History node did not save the booking reference"
    )

    return "History-saving function works independently"


if __name__ == "__main__":
    check("1. PROJECT FILES", inspect_files)

    imported = check("2. AGENT AND GRAPH", inspect_agent)

    if imported:
        check("3. HISTORY NODE UNIT TEST", test_history_node)

    print("\nDIAGNOSTIC COMPLETE")
    print("Review the first FAIL and its error message.")
