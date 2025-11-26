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
    product_records = client.command(
        module="Inventory",
        namespace="ProductRecords",
        command="GetProductRecords",
        body={
            "PartId": 100,
            "WarehouseId": 1,
            "HasBalance": False,
            "ChargeNumber": None
        },
        simulate=True,
    )
    print(product_records)

example()