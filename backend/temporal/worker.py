import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from .activities import (
    retrieve_support_context,
    generate_support_answer,
    save_support_result,
)

from .workflows import CustomerSupportWorkflow


async def main():

    client = await Client.connect(
        "localhost:7233"
    )

    worker = Worker(
        client,
        task_queue="holidaybreakz-support",
        workflows=[
            CustomerSupportWorkflow
        ],
        activities=[
            retrieve_support_context,
            generate_support_answer,
            save_support_result,
        ],
    )

    print("Temporal Worker started.")

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())