
import asyncio
import uuid
from datetime import timedelta

from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.common import RetryPolicy

TASK_QUEUE = "holidaybreakz-recovery-queue"


# 1. Activity with a simulated temporary failure
class SupportActivities:
    def __init__(self):
        self.attempt_counter = 0

    @activity.defn
    async def process_chat_escalation(self, session_id: str) -> str:
        self.attempt_counter += 1

        attempt = activity.info().attempt

        print(
            f"\n[Activity] Escalation for {session_id} "
            f"| Attempt #{attempt}"
        )

        # Simulate a temporary API failure on the first attempt
        if attempt == 1:
            print("[Activity] Simulating temporary API timeout...")
            raise RuntimeError(
                "API Timeout: OpenRouter or database connection failed."
            )

        print("[Activity] API connection recovered successfully.")

        return (
            f"Escalation resolved successfully "
            f"on attempt #{attempt}."
        )


# 2. Workflow with durable activity retries
@workflow.defn
class EscalationWorkflow:

    @workflow.run
    async def run(self, session_id: str) -> str:
        workflow.logger.info(
            f"Starting escalation workflow for session: {session_id}"
        )

        return await workflow.execute_activity(
            SupportActivities.process_chat_escalation,
            session_id,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=2),
                backoff_coefficient=2.0,
                maximum_attempts=3,
            ),
        )


# 3. Start worker and execute the test workflow
async def main():
    try:
        client = await Client.connect("127.0.0.1:7233")
    except Exception as exc:
        print(f"\nCould not connect to Temporal server: {exc}")
        print("Start the server with: temporal server start-dev")
        return

    activities = SupportActivities()
    workflow_id = f"escalation-test-{uuid.uuid4()}"

    print("\n" + "=" * 60)
    print("STARTING TEMPORAL WORKER & RECOVERY TEST")
    print("=" * 60)

    async with Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[EscalationWorkflow],
        activities=[activities.process_chat_escalation],
    ):
        try:
            result = await client.execute_workflow(
                EscalationWorkflow.run,
                "session-xyz-987",
                id=workflow_id,
                task_queue=TASK_QUEUE,
            )

            print("\nWORKFLOW COMPLETED SUCCESSFULLY!")
            print(f"Workflow ID: {workflow_id}")
            print(f"Final result: {result}")

        except Exception as exc:
            print(f"\nWorkflow failed: {exc!r}")


if __name__ == "__main__":
    asyncio.run(main())
