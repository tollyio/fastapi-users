import logging
from typing import Literal, Optional

from fastapi import Request, Response, status
from fastapi.security import APIKeyCookie
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi_users.authentication.transport.base import Transport
from fastapi_users.openapi import OpenAPIResponseType

logger = logging.getLogger(__name__)

class CookieTransport(Transport):
    scheme: APIKeyCookie

    def __init__(
        self,
        cookie_name: str = "fastapiusersauth",
        cookie_max_age: Optional[int] = None,
        cookie_path: str = "/",
        cookie_domain: Optional[str] = None,
        cookie_secure: bool = True,
        cookie_httponly: bool = True,
        cookie_samesite: Literal["lax", "strict", "none"] = "lax",
    ):
        self.cookie_name = cookie_name
        self.cookie_max_age = cookie_max_age
        self.cookie_path = cookie_path
        self.cookie_domain = cookie_domain
        self.cookie_secure = cookie_secure
        self.cookie_httponly = cookie_httponly
        self.cookie_samesite = cookie_samesite
        self.scheme = APIKeyCookie(name=self.cookie_name, auto_error=False)

    async def get_login_response(self, token: str, redirect_url: Optional[str] = None) -> Response:
        logger.info("Redirect to %s", redirect_url)

        redirect = RedirectResponse(
            url=redirect_url or "/"
        )
        return self._set_login_cookie(redirect, token)

    async def get_logout_response(self) -> Response:
        response = Response(status_code=status.HTTP_204_NO_CONTENT)
        return self._set_logout_cookie(response)
        
    async def handle_authentication_error_response(self, response: Response) -> Response:
        """
        Handle authentication errors by clearing the cookie.
        
        This method is called when authentication fails, ensuring that
        invalid cookies are cleared from the client.
        
        :param response: The response to modify
        :return: The modified response with cleared cookie
        """
        return self._set_logout_cookie(response)

    def _set_login_cookie(self, response: Response, token: str) -> Response:
        response.set_cookie(
            self.cookie_name,
            token,
            max_age=self.cookie_max_age,
            path=self.cookie_path,
            domain=self.cookie_domain,
            secure=self.cookie_secure,
            httponly=self.cookie_httponly,
            samesite=self.cookie_samesite,
        )
        return response

    def _set_logout_cookie(self, response: Response) -> Response:
        response.set_cookie(
            self.cookie_name,
            "",
            max_age=0,
            path=self.cookie_path,
            domain=self.cookie_domain,
            secure=self.cookie_secure,
            httponly=self.cookie_httponly,
            samesite=self.cookie_samesite,
        )
        return response

    @staticmethod
    def get_openapi_login_responses_success() -> OpenAPIResponseType:
        return {status.HTTP_307_TEMPORARY_REDIRECT: {"model": None}}

    @staticmethod
    def get_openapi_logout_responses_success() -> OpenAPIResponseType:
        return {status.HTTP_204_NO_CONTENT: {"model": None}}
