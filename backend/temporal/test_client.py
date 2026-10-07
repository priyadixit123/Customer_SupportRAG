import asyncio
import uuid

from temporalio.client import Client

from temporal.workflows import CustomerSupportWorkflow


async def main():

    client = await Client.connect(
        "localhost:7233"
    )

    question = "Can I select an aisle seat?"

    session_id = str(uuid.uuid4())

    result = await client.execute_workflow(
        CustomerSupportWorkflow.run,
        args=[question, session_id],
        id=f"holidaybreakz-{session_id}",
        task_queue="holidaybreakz-support",
    )

    print()
    print("=" * 60)
    print("TEMPORAL WORKFLOW RESULT")
    print("=" * 60)
    print("Question:", question)
    print("Answer:", result["answer"])
    print("Sources:", result["sources"])


if __name__ == "__main__":
    asyncio.run(main())