from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from contestdojo_api import auth, entities, events


def index(request):
    return JSONResponse({"hello": "world"})


app = Starlette(
    debug=True,
    routes=[
        Route("/", index),
        Mount("/entities", routes=entities.routes),
        Mount("/events", routes=events.routes),
    ],
    middleware=[auth.middleware],
)
