import functools
from typing import Any, Awaitable, Callable, TypedDict

from firebase_admin.auth import UserNotFoundError, UserRecord
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    AuthenticationError,
    BaseUser,
)
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from contestdojo_api.firebase import auth, firestore


class UserData(TypedDict):
    fname: str
    lname: str
    email: str
    type: str


class FirebaseUser(BaseUser, UserRecord):
    def __init__(self, user_record: UserRecord, user_data: UserData) -> None:
        super().__init__(user_record._data)
        self.data = user_data

    def is_authenticated(self) -> bool:
        return True


class FirebaseAuthBackend(AuthenticationBackend):
    async def authenticate(self, conn):
        try:
            auth_header = conn.headers["Authorization"]
        except KeyError:
            return

        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            return

        token_snap = await firestore.collection("api_tokens").document(token).get()
        token_data = token_snap.to_dict()
        if token_data is None:
            raise AuthenticationError

        try:
            user = auth.get_user(token_data["user"].id)
        except (ValueError, UserNotFoundError):
            raise AuthenticationError

        user_snap = await token_data["user"].get()
        user_data: UserData | None = user_snap.to_dict()  # type: ignore
        if user_data is None:
            raise AuthenticationError

        return AuthCredentials(), FirebaseUser(user, user_data)


def require_auth(*, type: str | None = None):
    def decorator(func: Callable[[Request, FirebaseUser], Awaitable[Any]]):
        @functools.wraps(func)
        async def wrapped(request: Request):
            if not request.user.is_authenticated:
                return JSONResponse({"error": "Unauthorized"}, status_code=401)
            if request.user.data["type"] != type:
                return JSONResponse({"error": "Forbidden"}, status_code=403)
            return await func(request, request.user)

        return wrapped

    return decorator


middleware = Middleware(AuthenticationMiddleware, backend=FirebaseAuthBackend())
