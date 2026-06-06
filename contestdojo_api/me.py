import asyncio

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from .firebase import db
from .oauth import require_scope
from .schemas import EventSchema, EventStudentSchema, EventTeamSchema


async def _my_student_docs(uid: str):
    """All event student (registration) docs belonging to the authenticated user."""
    user_ref = db.user(uid)
    return await db.client.collection_group("students").where("user", "==", user_ref).get()


@require_scope("events")
async def list_my_events(request: Request):
    student_docs = await _my_student_docs(request.user.uid)

    async def build(student):
        event_ref = student.reference.parent.parent
        if event_ref is None:
            return None
        event = await event_ref.get()
        if not event.exists:
            return None
        return {
            "event": EventSchema().dump_firestore(event),
            "student": EventStudentSchema(event=event).dump_firestore(student),
        }

    results = await asyncio.gather(*(build(s) for s in student_docs))
    return JSONResponse([r for r in results if r is not None])


@require_scope("teams")
async def list_my_teams(request: Request):
    student_docs = await _my_student_docs(request.user.uid)

    # Deduplicate by (event, team) since a user has one student record per event.
    seen: set[str] = set()
    tasks = []
    for student in student_docs:
        team_ref = student.to_dict().get("team")
        event_ref = student.reference.parent.parent
        if team_ref is None or event_ref is None:
            continue
        key = f"{event_ref.id}/{team_ref.id}"
        if key in seen:
            continue
        seen.add(key)
        tasks.append(_build_team(event_ref, team_ref))

    results = await asyncio.gather(*tasks)
    return JSONResponse([r for r in results if r is not None])


async def _build_team(event_ref, team_ref):
    event, team = await asyncio.gather(event_ref.get(), team_ref.get())
    if not event.exists or not team.exists:
        return None

    member_docs = await db.eventStudents(event.id).where("team", "==", team_ref).get()
    members = [EventStudentSchema(event=event).dump_firestore(m) for m in member_docs]

    return {
        "event": EventSchema().dump_firestore(event),
        "team": EventTeamSchema(event=event).dump_firestore(team),
        "members": members,
    }


routes = [
    Route("/events", list_my_events),
    Route("/teams", list_my_teams),
]
