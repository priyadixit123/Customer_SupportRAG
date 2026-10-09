
import asyncio
import sys
from temporalio.client import Client
from temporalio.api.enums.v1 import EventType


async def main():
    if len(sys.argv) < 2:
        print("Usage: python -m temporal.check_history WORKFLOW_ID")
        return

    workflow_id = sys.argv[1]
    client = await Client.connect("localhost:7233")
    handle = client.get_workflow_handle(workflow_id)

    print(f"Workflow ID: {workflow_id}")
    print("Reading Temporal history...\n")

    async for event in handle.fetch_history_events():
        try:
            event_type = EventType.Name(event.event_type)
        except ValueError:
            event_type = str(event.event_type)

        attrs_name = event.WhichOneof("attributes")
        details = ""

        if attrs_name:
            attrs = getattr(event, attrs_name)

            if hasattr(attrs, "activity_type"):
                details += f" | Activity: {attrs.activity_type.name}"

            if hasattr(attrs, "scheduled_event_id"):
                details += f" | Scheduled event: {attrs.scheduled_event_id}"

            if hasattr(attrs, "started_event_id"):
                details += f" | Started event: {attrs.started_event_id}"

            if hasattr(attrs, "attempt"):
                details += f" | Attempt: {attrs.attempt}"

        print(f"Event {event.event_id}: {event_type}{details}")


if __name__ == "__main__":
    asyncio.run(main())