from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from contestdojo_api.auth import FirebaseUser, require_auth
from contestdojo_api.firebase import db
from contestdojo_api.schemas import EntitySchema
from contestdojo_api.utils import chunks


@require_auth(type="admin")
async def list_entities(request: Request, user: FirebaseUser):
    entities = await db.entities.where("admins", "array_contains", db.user(user.uid)).get()
    return JSONResponse([EntitySchema().dump(x.to_dict()) for x in entities])


@require_auth(type="admin")
async def get_entity(request: Request, user: FirebaseUser):
    id = request.path_params["id"]
    entity = await db.entity(id).get()
    return JSONResponse(EntitySchema().dump(entity.to_dict()))


routes = [
    Route("/", list_entities),
    Route("/{id}", get_entity),
]
