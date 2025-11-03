import httpx
import logging
import time
from typing import Any

from .base_client import BaseClient, BatchCommandEntity
from .import exceptions as exc


logger = logging.getLogger(__name__)

class SyncClient(BaseClient):

    def __init__(self, company_number, username, password, base_url, language_code = "en", api_version = "v1", x_monitor_session_id = None, timeout = 10) -> None:
        super().__init__(company_number, username, password, base_url, language_code, api_version, x_monitor_session_id, timeout)
        self.client = httpx.Client(timeout=timeout, verify=False)
        self._login_happening = False

    def _make_api_request(self, request: httpx.Request) -> httpx.Response:
        if self._login_happening:
            logger.warning("Waiting for login to end...")
            while self._login_happening:
                time.sleep(0.01)
        try:
            response = None
            request = self._refresh_auth_header(request)
            logger.debug(f"Sending API request to {request.url!r}")
            response = self.client.send(request)
        except httpx.HTTPError as e:
            http_error = e.__doc__.strip() if e.__doc__ else e.__class__.__name__
            logger.error(f"API request http error: {http_error}")
            raise exc.RequestError()
        finally:
            self._log_request_response(request, response)

        if self._needs_retry(response):
            logger.warning(f"Retrying API request: {request.url!r}")
            self.login()
            try:
                response = None
                request = self._refresh_auth_header(request)
                logger.debug(f"Sending API request to {request.url!r}")
                response = self.client.send(request)
            except httpx.HTTPError as e:
                http_error = e.__doc__.strip() if e.__doc__ else e.__class__.__name__
                logger.error(f"API request http error: {http_error}")
                raise exc.RequestError()
            finally:
                self._log_request_response(request, response)
        
        return response

    def login(self) -> None:
        self._login_happening = True
        logger.warning("Performing login...")
        try:
            response = None
            request = self._create_login_request()
            try:
                response = self.client.send(request)
                self._handle_login_response(response)
            except httpx.HTTPError as e:
                http_error = e.__doc__.strip() if e.__doc__ else e.__class__.__name__
                logger.error(f"Login request http error: {http_error!r}")
                raise exc.RequestError()
        finally:
            self._log_request_response(request, response)
            self._login_happening = False

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
        skip: int | None = None
    ) -> Any:
        request = self._create_query_request(module, entity, id, language, filter, select, expand, orderby, top, skip)
        response = self._make_api_request(request)
        return self._handle_query_response(response)

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
        request = self._create_command_request(module, namespace, command, body, many, simulate, validate, language)
        response = self._make_api_request(request)
        return self._handle_command_response(response)

    def batch(self,
        commands: list[BatchCommandEntity],
        simulate: bool = False,
        validate: bool = False,
        language: str | None = None,
        raise_on_error: bool = False,
    ) -> Any:
        request = self._create_batch_request(commands, simulate, validate, language)
        response = self._make_api_request(request)
        return self._handle_batch_command_response(response, raise_on_error)