import json

from starlette.config import Config

config = Config(env_file=".env")

FIREBASE_CERTIFICATE = config("FIREBASE_CERTIFICATE", cast=json.loads)

# OIDC provider (the ContestDojo Next.js app) that issues OAuth JWT access tokens.
# The API acts as a resource server: it validates access tokens against the
# provider's JWKS and checks they were issued for this API (audience).
OIDC_ISSUER = config("OIDC_ISSUER")
OIDC_AUDIENCE = config("OIDC_AUDIENCE")
OIDC_JWKS_URI = config("OIDC_JWKS_URI", default=f"{OIDC_ISSUER}/jwks")
