from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from ..auth import require_auth
from ..firebase import db
from ..schemas import EntitySchema


@require_auth(type="admin")
async def list_entities(request: Request):
    entities = await db.entities.where("admins", "array_contains", db.user(request.user.uid)).get()
    return JSONResponse([EntitySchema().dump_firestore(x) for x in entities])


@require_auth(type="admin")
async def get_entity(request: Request):
    id = request.path_params["id"]
    entity = await db.entity(id).get()
    return JSONResponse(EntitySchema().dump_firestore(entity))


routes = [
    Route("/", list_entities),
    Route("/{id}", get_entity),
]
