# MonitorERP API Client

---

### Example:
<div class="termy">

```console
from monitorapi.sync_client import SyncClient

client = SyncClient(
    company_number="000.0",
    username="Username",
    password="Password",
    base_url="https://192.168.0.1:8001"
)

r = client.query(
    module="Inventory",
    entity="Parts",
    id=1,
)

```

</div>