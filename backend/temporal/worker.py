import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from temporal.activities import run_customer_support
from temporal.workflows import CustomerSupportWorkflow


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
            run_customer_support
        ],
    )

    print(
        "Temporal Worker started."
    )

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())