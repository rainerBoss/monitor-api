import os
from dotenv import load_dotenv
from monitor_api import MonitorAPI, MonitorAPIException

load_dotenv(".env", verbose=True, override=True)

m1 = MonitorAPI(
    company_number=os.environ["MONITOR_API_COMAPNY_NUMBER"],
    username=os.environ["MONITOR_API_USERNAME"],
    password=os.environ["MONITOR_API_PASSWORD"],
    host=os.environ["MONITOR_API_HOST"],
)

m1.authenticate()

data = m1.query("Common/RejectionCodeItems")
print(data)

data = m1.command("Common/Persons/GetIdByPersonalCardNumber", body={"PersonalCardNumber": ""})
print(data)