from temporalio import activity


@activity.defn
async def run_customer_support(
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