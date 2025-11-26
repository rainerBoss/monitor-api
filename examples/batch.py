import os
from dotenv import load_dotenv

from examples.config import logging_config
from monitorapi.sync_client import SyncClient

logging_config()
load_dotenv(".env")

def example() -> None:
    client = SyncClient(
        company_number=os.environ["API_COMPANY_NUMBER"],
        username=os.environ["API_USERNAME"],
        password=os.environ["API_PASSWORD"],
        base_url=os.environ["API_BASE_URL"],
    )
    batch_response = client.batch(
        commands=[
            {
                "Path": "Inventory/Parts/Create",
                "Body": {
                    "PartNumber": "TEST_PART_1",
                    "Description": "test part 1",
                    "Type": 0,
                    "StandardUnitId": 1,
                    "PartTemplateId": {"Value": 1},
                    "Update": None
                },
                "ForwardPropertyName": "EntityId",
                "ReceivingPropertyName": None,
            },
            {
                "Path": "Inventory/Parts/CreateHyperLink",
                "Body": {
                    "Link": "https://api.monitor.se/api/Monitor.API.Inventory.Commands.Parts.CreateHyperLink.html",
                    "Description": "test link"
                },
                "ForwardPropertyName": None,
                "ReceivingPropertyName": "PartId",
            }
        ],
        simulate=True,
        raise_on_error=True
    )
    print(batch_response)

example()