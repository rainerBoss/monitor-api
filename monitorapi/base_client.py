import httpx
import logging
from abc import ABC, abstractmethod
from typing import Any, TypedDict
from .import exceptions as exc


logger = logging.getLogger(__name__)

X_MONITOR_SESSION_ID_HEADER = "x-monitor-sessionid"

class BatchCommandEntity(TypedDict):
    Path: str
    Body: Any
    ForwardPropertyName: str | None
    ReceivingPropertyName: str | None

class BaseClient(ABC):

    def __init__(self,
        company_number: str,
        username: str,
        password: str,
        base_url: str,
        language_code: str = "en",
        api_version: str = "v1",
        x_monitor_session_id: str | None = None,
        timeout: int = 10
        ) -> None:
        self.company_number = company_number
        self.username = username
        self.password = password
        self.base_url = base_url

        self.language_code = language_code
        self.api_version = api_version
        self.x_monitor_session_id = x_monitor_session_id if x_monitor_session_id else "no-session-id-provided"

        self.timeout = timeout

    @staticmethod
    def _log_request_response(request: httpx.Request, response: httpx.Response | None = None) -> None:
        logger.debug(f"Request: {request.method!r} {request.url!r}")
        logger.debug(f"Request headers: {request.headers.raw}!r")
        logger.debug(f"Request body: {request.content!r}")
        if response:
            logger.debug(f"Response status: {response.status_code!r}")
            logger.debug(f"Response headers: {response.headers.raw!r}")
            logger.debug(f"Response body: {response.content!r}")

    def _create_login_request(self) -> httpx.Request:
        request = httpx.Request(
            method="POST",
            url=f"{self.base_url}/{self.language_code}/{self.company_number}/login",
            json={
                "Username": self.username,
                "Password": self.password,
                "ForceRelogin": True,
            }
        )
        return request

    def _handle_login_response(self, response: httpx.Response) -> None:
        if response.is_success:
            data = response.json()
            if data["SessionSuspended"]:
                logger.error(f"Session suspended: {response.text!r}")
                raise exc.SessionSuspended()
            else:
                self.x_monitor_session_id = response.headers.get(X_MONITOR_SESSION_ID_HEADER)
        else:
            logger.error(f"Login failed: {response.text!r}")
            raise exc.LoginFailed()
    
    def _refresh_auth_header(self, request: httpx.Request) -> httpx.Request:
        request.headers[X_MONITOR_SESSION_ID_HEADER] = self.x_monitor_session_id
        return request

    @abstractmethod
    def login(self) -> None:
        """
        Calls login endpoint and updates the X-Monitor-SessionId.

        Raises:
            RequestError and subtypes.
            AuthError and subtypes.
        """

    def _general_error_response_handler(self, response: httpx.Response) -> httpx.Response:
        """
        Check if response contains any documented general errors.
        These are not specific to Queries or Commands.
        Returns the response back for further handling if no error matched.
        """
        if response.status_code == 401:
            logger.error(f"Invalid session id: {response.text!r}")
            raise exc.InvalidSessionId()
        if response.status_code == 403:
            if response.text == "Monitor.API is not available for this system":
                logger.error(f"API not available: {response.text!r}")
                raise exc.ApiNotAvailable()
            else:
                logger.error(f"Session suspended: {response.text!r}")
                raise exc.SessionSuspended()
        if response.status_code == 500:
            logger.error(f"Unhandled exception: {response.text!r}")
            raise exc.UnhandledException()
        return response
    
    def _needs_retry(self, response: httpx.Response) -> bool:
        if response.status_code == 401:
            return True
        return False

    def _create_query_request(self,
        module: str,
        entity: str,
        id: int | None = None,
        language: str | None  = None,
        filter: str  | None = None,
        select: str | None = None,
        expand: str | None = None,
        orderby: str | None = None,
        top: int | None = None,
        skip: int | None = None
    ) -> httpx.Request:
        if not language:
            language = self.language_code

        if id is None:
            _id = ''
        else:
            _id = f"/{_id}"

        params: dict[str, str] = {}
        if filter is not None:
            params["$filter"] = filter
        if select is not None:
            params["$select"] = select
        if expand is not None:
            params["$expand"] = expand
        if orderby is not None:
            params["$orderby"] = orderby
        if top is not None:
            params["$top"] = str(top)
        if skip is not None:
            params["$skip"] = str(skip)

        request = httpx.Request(
            method="POST",
            headers={
                X_MONITOR_SESSION_ID_HEADER: self.x_monitor_session_id,
                "Accept": "application/json",
                "Content-Type": "x-www-form-urlencoded"
            },
            url=f"{self.base_url}/{language}/{self.company_number}/api/{self.api_version}/{module}/{entity}{_id}",
            data=params,
        )
        return request
    
    @abstractmethod
    def query(self,
        module: str,
        entity: str,
        id: int | None = None,
        language: str | None  = None,
        filter: str  | None = None,
        select: str | None = None,
        expand: str | None = None,
        orderby: str | None = None,
        top: int | None = None,
        skip: int | None = None,
    ) -> Any:
        """
        Calls MonitorERP API query interface.
        Queries are sent to the API using HTTP GET requests with query parameters that manipulate the way data is fetched and returned.
        They bypass the business domain providing very fast read access of the persistent data of the MonitorERP system.
        
        Raises:
            RequestError and subtypes
            GeneralError and subtypes
            QueryError and subtypes
        """
    
    def _handle_query_response(self, response: httpx.Response) -> Any:
        if response.is_success:
            return response.json()
        else:
            if response.status_code == 400:
                if "Id" in response.text:
                    logger.error(f"Invalid query id: {response.text!r}")
                    raise exc.QueryInvalidId()
                else:
                    logger.error(f"Invalid query filter: {response.text!r}")
                    raise exc.QueryInvalidFilter()
            if response.status_code == 404:
                logger.error(f"Query entity not found: {response.text!r}")
                raise exc.QueryEntityNotFound()
            response = self._general_error_response_handler(response)
            logger.error(f"Query error: {response.text!r}")
            raise exc.QueryError()

    def _create_command_request(self,
        module: str,
        namespace: str,
        command: str,
        body: Any | None = None,
        many: bool = False,
        simulate: bool = False,
        validate: bool = False,
        language: str | None = None,
    ) -> httpx.Request:
        if not language:
            language = self.language_code
        
        sim_or_val = ""
        if simulate is True:
            sim_or_val = "/Simulate"
        if validate is True:
            sim_or_val = "/Validate"
        
        _many = ""
        if many is True:
            _many = "/Many"
        
        request = httpx.Request(
            method="POST",
            headers={
                X_MONITOR_SESSION_ID_HEADER: self.x_monitor_session_id,
            },
            url=f"{self.base_url}/{language}/{self.company_number}/api/{self.api_version}/{module}/{namespace}/{command}{_many}{sim_or_val}",
            json=body,
        )
        return request

    @abstractmethod
    def command(self,
        module: str,
        namespace: str,
        command: str,
        many: bool = False,
        simulate: bool = False,
        validate: bool = False,
        language: str | None = None,
        body: Any | None = None
    ) -> Any:
        """
        Calls MonitorERP API command interface.
        Commands are sent to the API using HTTP POST requests.
        Commands interact with the business domain of the MonitorERP system.

        Raises:
            RequestError and subtypes
            GeneralError and subtypes
            QueryError and subtypes
        """

    def _handle_command_response(self, response: httpx.Response) -> Any:
        if response.is_success:
            if not response.content:
                return None
            else:
                return response.json()
        else:
            if response.status_code == 400:
                logger.error(f"Command validation failure: {response.text!r}")
                raise exc.CommandValidationFailure()
            if response.status_code == 404:
                if "id" in response.text:
                    logger.error(f"Command entity not found: {response.text!r}")
                    raise exc.CommandEntityNotFound()
                else:
                    logger.error(f"Command not found: {response.text!r}")
                    raise exc.CommandNotFound()
            if response.status_code == 409:
                logger.error(f"Command conflict: {response.text!r}")
                raise exc.CommandConflict()
            response = self._general_error_response_handler(response)
            logger.error(f"Command error: {response.text!r}")
            raise exc.CommandError()

    def _create_batch_request(self,
        commands: list[BatchCommandEntity],
        simulate: bool = False,
        validate: bool = False,
        language: str | None = None,
    ) -> Any:
        if not language:
            language = self.language_code

        sim_or_val = ""
        if simulate is True:
            sim_or_val = "/Simulate"
        if validate is True:
            sim_or_val = "/Validate"
        
        request = httpx.Request(
            method="POST",
            headers={
                X_MONITOR_SESSION_ID_HEADER: self.x_monitor_session_id
            },
            url=f"{self.base_url}/{language}/{self.company_number}/api/{self.api_version}/Batch{sim_or_val}",
            json=commands,
        )
        return request
    

    @abstractmethod
    def batch(self,
        commands: list[BatchCommandEntity],
        simulate: bool = False,
        validate: bool = False,
        language: str | None = None,
        raise_on_error: bool = False,
    ) -> Any: pass
    
    def _handle_batch_command_response(self, response: httpx.Response, raise_on_error: bool) -> Any:
        if response.is_success:
            batch_response = response.json()
            if "IsSuccessful" in batch_response and not batch_response["IsSuccessful"] and raise_on_error:
                error_message = batch_response["ErrorMessage"]
                failing_index = batch_response["FailingIndex"]
                logger.error(f"Batch command error at index {failing_index}: {error_message}")
                raise exc.BatchCommandError(f"At index {failing_index}: {error_message}")
            else:
                return batch_response
        else:
            return self._handle_command_response(response)