import httpx
import logging
import json

logger = logging.getLogger(__name__)

class MonitorAPIException(Exception):
    def __init__(self, message: str, status="", content="") -> None:
        self.message = message
        self.status = status
        self.content = content
        super().__init__(message)

    def __repr__(self) -> str:
        return f"{self.message}: status `{self.status}` content `{self.content}`"

    def __str__(self) -> str:
        return f"{self.message}: status `{self.status}` content `{self.content}`"


class MonitorAPI:
    def __init__(self, company_number: str, username: str, password: str, host, port: int=8001, language_code="en", api_version="v1", force_relogin=False) -> None:
        self.port = port
        self.host = host
        self.company_number = company_number
        self.username = username
        self.password = password
        self.language_code = language_code
        self.api_version = api_version
        self.force_relogin = force_relogin
        self.session_id = None

        self.client = httpx.Client(verify=False, timeout=5)

    @property
    def base_url(self):
        return f"https://{self.host}:{self.port}/{self.language_code}/{self.company_number}"

    def log_response(self, data, name="response"):
        with open(f"logs/{name}.json", "w", encoding="utf-8") as file:
            file.write(json.dumps(data, indent=4, ensure_ascii=False))

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        try:
            response = self.client.send(request)
        except (httpx.ConnectTimeout) as e:
            raise MonitorAPIException("Connection timeout")
        except (httpx.ConnectError) as e:
            raise MonitorAPIException("Connection error")
        else:
            return response

    def handle_response(self, r: httpx.Response):
        try:
            data = r.json()
        except json.decoder.JSONDecodeError as e:
            data = r.text
        finally:
            self.log_response(data, r.status_code)
        if r.status_code == 200:
            return data
        elif r.status_code == 400:
            raise MonitorAPIException("Bad request", status=r.status_code, content=data)
        elif r.status_code == 401:
            raise MonitorAPIException("Unauthorized", status=r.status_code, content=data)
        elif r.status_code == 403:
            raise MonitorAPIException("Forbidden", status=r.status_code, content=data)
        elif r.status_code == 404:
            raise MonitorAPIException("Query/Command not found", status=r.status_code, content=data)
        elif r.status_code == 409:
            raise MonitorAPIException("Command conflict", status=r.status_code, content=data)
        elif r.status_code == 500:
            raise MonitorAPIException("Server error", status=r.status_code, content=data)
        else:
            raise MonitorAPIException("Unexpected error", status=r.status_code, content=data)

    def authenticate(self):
        response = self.handle_request(httpx.Request(
            method="POST",
            url=f"{self.base_url}/login",
            json={
                "Username": self.username,
                "Password": self.password,
                "ForceRelogin": self.force_relogin,
            }
        ))
        data = self.handle_response(response)
        if self.force_relogin:
            self.session_id = data["SessionId"]
        else:
            if data["ActiveSessions"]:
                self.session_id = data["ActiveSessions"][0]["SessionIdentifier"]
        return data
    
    def query(self, query: str):
        response = self.handle_request(httpx.Request(
            method="GET",
            url=f"{self.base_url}/api/{self.api_version}/{query}",
            headers={
                "X-Monitor-SessionId": f"{self.session_id}"
            }
        ))
        data = self.handle_response(response)
        return data

    def command(self, command: str, body=None):
        response = self.handle_request(httpx.Request(
            method="POST",
            url=f"{self.base_url}/api/{self.api_version}/{command}",
            headers={
                "X-Monitor-SessionId": f"{self.session_id}"
            },
            json=body,
        ))
        data = self.handle_response(response)
        return data