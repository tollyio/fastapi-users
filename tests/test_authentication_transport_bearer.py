import pytest
from fastapi import status, Request
from fastapi.responses import JSONResponse
from fastapi_users.authentication.transport import (
    BearerTransport,
    TransportLogoutNotSupportedError,
)
from fastapi_users.authentication.transport.bearer import BearerResponse


@pytest.fixture()
def bearer_transport() -> BearerTransport:
    return BearerTransport(tokenUrl="/login")

@pytest.mark.authentication
@pytest.mark.asyncio
async def test_get_login_response(bearer_transport: BearerTransport, redirect_url: str):
    response = await bearer_transport.get_login_response("TOKEN", redirect_url)

    assert isinstance(response, JSONResponse)
    assert response.body == b'{"access_token":"TOKEN","token_type":"bearer"}'


@pytest.mark.authentication
@pytest.mark.asyncio
async def test_get_logout_response(bearer_transport: BearerTransport):
    with pytest.raises(TransportLogoutNotSupportedError):
        await bearer_transport.get_logout_response()


@pytest.mark.authentication
@pytest.mark.openapi
def test_get_openapi_login_responses_success(bearer_transport: BearerTransport):
    openapi_responses = bearer_transport.get_openapi_login_responses_success()
    assert openapi_responses[status.HTTP_200_OK]["model"] == BearerResponse


@pytest.mark.authentication
@pytest.mark.openapi
def test_get_openapi_logout_responses_success(bearer_transport: BearerTransport):
    openapi_responses = bearer_transport.get_openapi_logout_responses_success()
    assert openapi_responses == {}
