from typing import Protocol, Optional

from fastapi import Response
from fastapi.security.base import SecurityBase

from fastapi_users.openapi import OpenAPIResponseType


class TransportLogoutNotSupportedError(Exception):
    pass


class Transport(Protocol):
    scheme: SecurityBase

    async def get_login_response(self, token: str, redirect_url: Optional[str] = None) -> Response: ...  # pragma: no cover

    async def get_logout_response(self) -> Response: ...  # pragma: no cover

    async def handle_authentication_error_response(self, response: Response) -> Response: 
        """
        Process a response for authentication errors.
        
        This method should modify the response as needed (e.g., clearing cookies)
        and return the modified response.
        
        :param response: The response to modify
        :return: The modified response
        """
        return response

    @staticmethod
    def get_openapi_login_responses_success() -> OpenAPIResponseType:
        """Return a dictionary to use for the openapi responses route parameter."""
        ...  # pragma: no cover

    @staticmethod
    def get_openapi_logout_responses_success() -> OpenAPIResponseType:
        """Return a dictionary to use for the openapi responses route parameter."""
        ...  # pragma: no cover
