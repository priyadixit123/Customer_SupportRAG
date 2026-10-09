
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from .activities import (
        retrieve_support_context,
        generate_support_answer,
        save_support_result,
    )


@workflow.defn
class CustomerSupportWorkflow:

    @workflow.run
    async def run(
        self,
        question: str,
        session_id: str
    ) -> dict:

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=30),
            maximum_attempts=3,
        )

        context = await workflow.execute_activity(
            retrieve_support_context,
            args=[question, session_id],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
        )

        answer = await workflow.execute_activity(
            generate_support_answer,
            args=[context],
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=retry_policy,
        )

        result = await workflow.execute_activity(
            save_support_result,
            args=[answer],
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=retry_policy,
        )

        return result
