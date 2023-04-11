import asyncio

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from ..auth import FirebaseUser, require_auth
from ..firebase import db
from ..schemas import EventSchema
from ..utils import chunks


@require_auth(type="admin")
async def list_events(request: Request, user: FirebaseUser):
    entities = await db.entities.where("admins", "array_contains", db.user(user.uid)).get()
    fetchEventChunks = [
        db.events.where("owner", "in", [x.reference for x in ch]).get()
        for ch in chunks(entities, 10)
    ]
    eventChunks = await asyncio.gather(*fetchEventChunks)
    events = [x for ch in eventChunks for x in ch]
    return JSONResponse([EventSchema().dump_firestore(x) for x in events])


@require_auth(type="admin")
async def get_event(request: Request, user: FirebaseUser):
    id = request.path_params["id"]
    event = await db.event(id).get()
    return JSONResponse(EventSchema().dump_firestore(event))


routes = [
    Route("/", list_events),
    Route("/{id}", get_event),
]
