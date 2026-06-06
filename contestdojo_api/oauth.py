import functools
from typing import Any, Awaitable, Callable

import jwt
from jwt import PyJWKClient
from starlette.authentication import AuthCredentials, BaseUser
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import JSONResponse

from . import settings

__all__ = ("OAuthUser", "authenticate_oauth", "require_scope")


# Access tokens are JWTs minted by the ContestDojo OIDC provider (the Next.js app).
# We validate them statelessly against the provider's published JWKS, so no shared
# secret or network round-trip to the provider is needed per request (keys are cached).
_jwk_client = PyJWKClient(settings.OIDC_JWKS_URI)


class OAuthUser(BaseUser):
    def __init__(self, claims: dict[str, Any]) -> None:
        self.claims = claims
        self.uid: str = claims["sub"]
        scope = claims.get("scope") or ""
        self.scopes: set[str] = set(scope.split())

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return self.uid

    @property
    def identity(self) -> str:
        return self.uid


def _decode(token: str) -> dict[str, Any]:
    signing_key = _jwk_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=settings.OIDC_AUDIENCE,
        issuer=settings.OIDC_ISSUER,
        options={"require": ["exp", "iat", "sub"]},
    )


async def authenticate_oauth(token: str) -> tuple[AuthCredentials, OAuthUser] | None:
    """Validate an OIDC JWT access token. Returns None if the token is not a valid
    access token from the provider (signature/issuer/audience/expiry checks)."""

    try:
        claims = await run_in_threadpool(_decode, token)
    except (jwt.InvalidTokenError, jwt.PyJWKClientError):
        return None

    user = OAuthUser(claims)
    return AuthCredentials(list(user.scopes)), user


def require_scope(scope: str):
    """Gate a route behind an OIDC access token carrying the given scope."""

    def decorator(func: Callable[[Request], Awaitable[Any]]):
        @functools.wraps(func)
        async def wrapped(request: Request):
            user = request.user
            if not isinstance(user, OAuthUser):
                return JSONResponse({"error": "Unauthorized"}, status_code=401)
            if scope not in user.scopes:
                return JSONResponse(
                    {"error": f"Insufficient scope: '{scope}' required"},
                    status_code=403,
                )
            return await func(request)

        return wrapped

    return decorator
