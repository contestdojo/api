from marshmallow import ValidationError
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from . import auth, entities, events


def index(request):
    return JSONResponse({"hello": "world"})


def handle_marshmallow_validation_error(request, exc):
    return JSONResponse({"errors": exc.messages}, status_code=400)


app = Starlette(
    debug=True,
    routes=[
        Route("/", index),
        Mount("/entities", routes=entities.routes),
        Mount("/events", routes=events.routes),
    ],
    middleware=[Middleware(ProxyHeadersMiddleware), auth.middleware],
    exception_handlers={ValidationError: handle_marshmallow_validation_error},
)
