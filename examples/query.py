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
    parts = client.query(
        module="Inventory",
        entity="Parts",
        expand="PackageType",
        select="Id,PartNumber",
        filter="strcontains(PartNumber,69)",
        orderby="PartNumber desc",
        top=5,
        skip=50,
    )
    for part in parts:
        print(part)

    language_codes = client.query(
        module="Common",
        entity="LanguageCodes",
        select="Code",
        post=True,
    )
    codes = [code["Code"] for code in language_codes] 
    print(codes)
    
    rejection_codes = client.query(
        module="Common",
        entity="RejectionCodeItems",
        language=next(iter(codes)),
    )    
    print(rejection_codes)


example()