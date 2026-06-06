from marshmallow import ValidationError
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from . import auth, entities, events, me, openapi


def index(request):
    return JSONResponse({"hello": "world"})


def handle_marshmallow_validation_error(request, exc):
    return JSONResponse({"errors": exc.messages}, status_code=400)


app = Starlette(
    debug=False,
    routes=[
        Route("/", index),
        Mount("/entities", routes=entities.routes),
        Mount("/events", routes=events.routes),
        Mount("/v1alpha1/me", routes=me.routes),
        *openapi.routes,
    ],
    middleware=[Middleware(ProxyHeadersMiddleware), auth.middleware],
    exception_handlers={ValidationError: handle_marshmallow_validation_error},
)
