from collections.abc import Sequence
from typing import Generic, Optional

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.responses import JSONResponse

from fastapi_users import models, schemas
from fastapi_users.authentication import AuthenticationBackend, Authenticator
from fastapi_users.authentication.authenticator import AuthenticationRequiredError
from fastapi_users.jwt import SecretType
from fastapi_users.manager import UserManagerDependency
from fastapi_users.router import (
    get_auth_router,
    get_register_router,
    get_reset_password_router,
    get_users_router,
    get_verify_router,
)

try:
    from httpx_oauth.oauth2 import BaseOAuth2

    from fastapi_users.router import get_oauth_router
    from fastapi_users.router.oauth import get_oauth_associate_router
except ModuleNotFoundError:  # pragma: no cover
    BaseOAuth2 = type  # type: ignore


class FastAPIUsers(Generic[models.UP, models.ID]):
    """
    Main object that ties together the component for users authentication.

    :param get_user_manager: Dependency callable getter to inject the
    user manager class instance.
    :param auth_backends: List of authentication backends.

    :attribute current_user: Dependency callable getter to inject authenticated user
    with a specific set of parameters.
    """

    authenticator: Authenticator[models.UP, models.ID]

    def __init__(
        self,
        get_user_manager: UserManagerDependency[models.UP, models.ID],
        auth_backends: Sequence[AuthenticationBackend[models.UP, models.ID]],
    ):
        self.authenticator = Authenticator(auth_backends, get_user_manager)
        self.get_user_manager = get_user_manager
        self.current_user = self.authenticator.current_user

    def get_register_router(
        self, user_schema: type[schemas.U], user_create_schema: type[schemas.UC]
    ) -> APIRouter:
        """
        Return a router with a register route.

        :param user_schema: Pydantic schema of a public user.
        :param user_create_schema: Pydantic schema for creating a user.
        """
        return get_register_router(
            self.get_user_manager, user_schema, user_create_schema
        )

    def get_verify_router(self, user_schema: type[schemas.U]) -> APIRouter:
        """
        Return a router with e-mail verification routes.

        :param user_schema: Pydantic schema of a public user.
        """
        return get_verify_router(self.get_user_manager, user_schema)

    def get_reset_password_router(self) -> APIRouter:
        """Return a reset password process router."""
        return get_reset_password_router(self.get_user_manager)

    def get_auth_router(
        self,
        backend: AuthenticationBackend[models.UP, models.ID],
        requires_verification: bool = False,
    ) -> APIRouter:
        """
        Return an auth router for a given authentication backend.

        :param backend: The authentication backend instance.
        :param requires_verification: Whether the authentication
        require the user to be verified or not. Defaults to False.
        """
        return get_auth_router(
            backend,
            self.get_user_manager,
            self.authenticator,
            requires_verification,
        )

    def get_oauth_router(
        self,
        oauth_client: BaseOAuth2,
        backend: AuthenticationBackend[models.UP, models.ID],
        state_secret: SecretType,
        redirect_url: Optional[str] = None,
        associate_by_email: bool = False,
        is_verified_by_default: bool = False,
    ) -> APIRouter:
        """
        Return an OAuth router for a given OAuth client and authentication backend.

        :param oauth_client: The HTTPX OAuth client instance.
        :param backend: The authentication backend instance.
        :param state_secret: Secret used to encode the state JWT.
        :param redirect_url: Optional arbitrary redirect URL for the OAuth2 flow.
        If not given, the URL to the callback endpoint will be generated.
        :param associate_by_email: If True, any existing user with the same
        e-mail address will be associated to this user. Defaults to False.
        :param is_verified_by_default: If True, the `is_verified` flag will be
        set to `True` on newly created user. Make sure the OAuth Provider you're
        using does verify the email address before enabling this flag.
        """
        return get_oauth_router(
            oauth_client,
            backend,
            self.get_user_manager,
            state_secret,
            redirect_url,
            associate_by_email,
            is_verified_by_default,
        )

    def get_oauth_associate_router(
        self,
        oauth_client: BaseOAuth2,
        user_schema: type[schemas.U],
        state_secret: SecretType,
        redirect_url: Optional[str] = None,
        requires_verification: bool = False,
    ) -> APIRouter:
        """
        Return an OAuth association router for a given OAuth client.

        :param oauth_client: The HTTPX OAuth client instance.
        :param user_schema: Pydantic schema of a public user.
        :param state_secret: Secret used to encode the state JWT.
        :param redirect_url: Optional arbitrary redirect URL for the OAuth2 flow.
        If not given, the URL to the callback endpoint will be generated.
        :param requires_verification: Whether the endpoints
        require the users to be verified or not. Defaults to False.
        """
        return get_oauth_associate_router(
            oauth_client,
            self.authenticator,
            self.get_user_manager,
            user_schema,
            state_secret,
            redirect_url,
            requires_verification,
        )

    def get_users_router(
        self,
        user_schema: type[schemas.U],
        user_update_schema: type[schemas.UU],
        requires_verification: bool = False,
    ) -> APIRouter:
        """
        Return a router with routes to manage users.

        :param user_schema: Pydantic schema of a public user.
        :param user_update_schema: Pydantic schema for updating a user.
        :param requires_verification: Whether the endpoints
        require the users to be verified or not. Defaults to False.
        """
        return get_users_router(
            self.get_user_manager,
            user_schema,
            user_update_schema,
            self.authenticator,
            requires_verification,
        )
        
    async def authentication_exception_handler(
        self, request: Request, exc: AuthenticationRequiredError
    ) -> Response:
        """
        Handle authentication exceptions by using the appropriate transport's error handling.
        
        This handler is called when an AuthenticationRequiredError is raised during
        the authentication process. It uses the transport's handle_authentication_error_response
        method to properly handle authentication failures (e.g., clearing cookies).
        
        :param request: The FastAPI request object
        :param exc: The AuthenticationRequiredError exception
        :return: A Response object
        """
        # Create a base response
        response = JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
        
        # If we know which backend failed, use its transport
        if exc.backend is not None:
            response = await exc.backend.transport.handle_authentication_error_response(response)
        else:
            # Otherwise, let all transports handle the response
            # This ensures that any transport-specific cleanup (like cookie clearing) happens
            for backend in self.authenticator.backends:
                response = await backend.transport.handle_authentication_error_response(response)
                
        return response
        
    def add_auth_exception_handler(self, app: FastAPI) -> None:
        """
        Register the authentication exception handler with a FastAPI application.
        
        This method should be called after creating your FastAPI app to enable
        proper handling of authentication errors, including clearing cookies
        when authentication fails.
        
        :param app: The FastAPI application instance
        """
        app.add_exception_handler(
            AuthenticationRequiredError, 
            self.authentication_exception_handler
        )
