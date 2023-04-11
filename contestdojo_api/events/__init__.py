import asyncio

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from ..auth import require_auth
from ..firebase import db
from ..schemas import EventSchema
from ..utils import chunks
from . import event
from .decorators import fetch_event


@require_auth(type="admin")
async def list_events(request: Request):
    entities = await db.entities.where("admins", "array_contains", db.user(request.user.uid)).get()
    fetchEventChunks = [
        db.events.where("owner", "in", [x.reference for x in ch]).get()
        for ch in chunks(entities, 10)
    ]
    eventChunks = await asyncio.gather(*fetchEventChunks)
    events = [x for ch in eventChunks for x in ch]
    return JSONResponse([EventSchema().dump_firestore(x) for x in events])


@require_auth(type="admin")
@fetch_event()
async def get_event(request: Request):
    return JSONResponse(EventSchema().dump_firestore(request.event))


routes = [
    Route("/", list_events),
    Route("/{event_id}", get_event),
    Mount("/{event_id}", routes=event.routes),
]
