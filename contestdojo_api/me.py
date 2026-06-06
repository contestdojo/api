import asyncio

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from .firebase import db
from .oauth import require_scope
from .schemas import EventSchema, EventStudentSchema, TeamRefSchema


async def _my_student_docs(uid: str):
    """All event student (registration) docs belonging to the authenticated user."""
    user_ref = db.user(uid)
    return await db.client.collection_group("students").where("user", "==", user_ref).get()


async def _my_student_in_event(uid: str, event_id: str):
    """The authenticated user's registration in one event, or None.

    The student doc id is not the user's uid, so it is located by the `user`
    reference field within the event's students subcollection.
    """
    user_ref = db.user(uid)
    docs = await db.eventStudents(event_id).where("user", "==", user_ref).limit(1).get()
    return docs[0] if docs else None


async def _team_ref(event_ref, team_ref):
    """A minimal reference to the user's team: id + name only.

    The team's other members are intentionally not exposed -- the access token
    only carries this user's consent, so other students' records stay private.
    """
    if team_ref is None:
        return None
    team = await team_ref.get()
    if not team.exists:
        return None
    return TeamRefSchema().dump_firestore(team)


async def _participation(student):
    """Build the {event, registration, team} envelope for one student doc."""
    event_ref = student.reference.parent.parent
    if event_ref is None:
        return None
    event = await event_ref.get()
    if not event.exists:
        return None
    team = await _team_ref(event_ref, student.to_dict().get("team"))
    return {
        "event": EventSchema().dump_firestore(event),
        "registration": EventStudentSchema(event=event).dump_firestore(student),
        "team": team,
    }


@require_scope("read:events")
async def list_my_events(request: Request):
    student_docs = await _my_student_docs(request.user.uid)
    results = await asyncio.gather(*(_participation(s) for s in student_docs))
    return JSONResponse([r for r in results if r is not None])


@require_scope("read:events")
async def get_my_event(request: Request):
    event_id = request.path_params["event_id"]
    student = await _my_student_in_event(request.user.uid, event_id)
    if student is None:
        return JSONResponse({"error": "Not found"}, status_code=404)
    result = await _participation(student)
    if result is None:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse(result)


routes = [
    Route("/events", list_my_events),
    Route("/events/{event_id}", get_my_event),
]
