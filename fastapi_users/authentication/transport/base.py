from typing import Protocol

from fastapi import Request, Response
from fastapi.security.base import SecurityBase

from fastapi_users.openapi import OpenAPIResponseType


class TransportLogoutNotSupportedError(Exception):
    pass


class Transport(Protocol):
    scheme: SecurityBase

    async def get_login_response(self, token: str, request: Request) -> Response: ...  # pragma: no cover

    async def get_logout_response(self, request: Request) -> Response: ...  # pragma: no cover

    @staticmethod
    def get_openapi_login_responses_success() -> OpenAPIResponseType:
        """Return a dictionary to use for the openapi responses route parameter."""
        ...  # pragma: no cover

    @staticmethod
    def get_openapi_logout_responses_success() -> OpenAPIResponseType:
        """Return a dictionary to use for the openapi responses route parameter."""
        ...  # pragma: no cover
