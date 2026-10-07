from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from .activities import run_customer_support


@workflow.defn
class CustomerSupportWorkflow:

    @workflow.run
    async def run(
        self,
        question: str,
        session_id: str
    ) -> dict:

        result = await workflow.execute_activity(
            run_customer_support,
            args=[question, session_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(
                maximum_attempts=3
            )
        )

        return result