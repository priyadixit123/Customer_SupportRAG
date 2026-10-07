from temporalio.client import Client


async def get_temporal_client():

    client = await Client.connect(
        "localhost:7233"
    )

    return client