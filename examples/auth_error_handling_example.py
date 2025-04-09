from typing import Optional

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    CookieTransport,
    JWTStrategy,
)
from fastapi_users.authentication.authenticator import AuthenticationRequiredError

# Import your user model, database setup, etc.
# This is just an example structure
from examples.db import User, get_user_db
from examples.schemas import UserCreate, UserRead, UserUpdate


# JWT authentication strategy
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret="your-secret-key", lifetime_seconds=3600)


# Cookie transport
cookie_transport = CookieTransport(
    cookie_name="fastapiusers_auth",
    cookie_max_age=3600,
    cookie_secure=True,
    cookie_httponly=True,
)

# Authentication backend
auth_backend = AuthenticationBackend(
    name="cookie",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)


# FastAPI Users instance
fastapi_users = FastAPIUsers[User, int](
    get_user_db,
    [auth_backend],
)


# Create FastAPI app
app = FastAPI()

# Add authentication routes
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/cookie",
    tags=["auth"],
)

# Register the authentication exception handler
# This is the key part that ensures cookies are cleared when authentication fails
fastapi_users.add_auth_exception_handler(app)


# Protected route example
@app.get("/protected-route")
def protected_route(user: User = Depends(fastapi_users.current_user())):
    return {"message": f"Hello, {user.email}"}
