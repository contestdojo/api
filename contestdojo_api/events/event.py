import asyncio

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from ..auth import require_auth
from ..firebase import db
from ..schemas import EventOrganizationSchema, EventStudentSchema, EventTeamSchema, OrganizationSchema
from .decorators import fetch_event


@require_auth(type="admin")
@fetch_event()
async def list_event_orgs(request: Request):
    results, rootOrgs = await asyncio.gather(db.eventOrgs(request.event.id).get(), db.orgs.get())
    rootOrgs = {x.id: x for x in rootOrgs}
    merged = [
        {
            **EventOrganizationSchema(request.event).dump_firestore(x),
            **OrganizationSchema().dump_firestore(rootOrgs[x.id]),
        }
        for x in results
    ]
    return JSONResponse(merged)


@require_auth(type="admin")
@fetch_event()
async def get_event_org(request: Request):
    id = request.path_params["org_id"]
    root_result = await db.org(id).get()
    result = await db.eventOrg(request.event.id, id).get()
    if not result.exists:
        return JSONResponse({"error": "Not found"}, status_code=404)
    result = {
        "id": result.id,
        "name": root_result.to_dict()["name"],
        **result.to_dict(),
    }
    return JSONResponse(EventOrganizationSchema(request.event).dump(result))


@require_auth(type="admin")
@fetch_event()
async def update_event_org(request: Request):
    schema = EventOrganizationSchema(request.event)
    update = schema.load(await request.json())
    ref = db.eventOrg(request.event.id, request.path_params["org_id"])
    if not (await ref.get()).exists:
        return JSONResponse({"error": "Not found"}, status_code=404)
    await ref.set(update, merge=True)
    result = await ref.get()
    return JSONResponse(schema.dump_firestore(result))


@require_auth(type="admin")
@fetch_event()
async def delete_event_org(request: Request):
    await db.eventOrg(request.event.id, request.path_params["org_id"]).delete()
    return Response(status_code=204)


@require_auth(type="admin")
@fetch_event()
async def list_event_teams(request: Request):
    ref = db.eventTeams(request.event.id)
    if org_id := request.query_params.get("org"):
        ref = ref.where("org", "==", db.org(org_id))
    if number := request.query_params.get("number"):
        ref = ref.where("number", "==", number)
    results = await ref.get()
    return JSONResponse([EventTeamSchema(request.event).dump_firestore(x) for x in results])


@require_auth(type="admin")
@fetch_event()
async def get_event_team(request: Request):
    id = request.path_params["team_id"]
    result = await db.eventTeam(request.event.id, id).get()
    if not result.exists:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse(EventTeamSchema(request.event).dump_firestore(result))


@require_auth(type="admin")
@fetch_event()
async def update_event_team(request: Request):
    schema = EventTeamSchema(request.event)
    update = schema.load(await request.json())
    ref = db.eventTeam(request.event.id, request.path_params["team_id"])
    if not (await ref.get()).exists:
        return JSONResponse({"error": "Not found"}, status_code=404)
    await ref.set(update, merge=True)
    result = await ref.get()
    return JSONResponse(schema.dump_firestore(result))


@require_auth(type="admin")
@fetch_event()
async def delete_event_team(request: Request):
    await db.eventTeam(request.event.id, request.path_params["team_id"]).delete()
    return Response(status_code=204)


@require_auth(type="admin")
@fetch_event()
async def list_event_students(request: Request):
    ref = db.eventStudents(request.event.id)
    if org_id := request.query_params.get("org"):
        ref = ref.where("org", "==", db.org(org_id))
    if team_id := request.query_params.get("team"):
        ref = ref.where("team", "==", db.eventTeam(request.event.id, team_id))
    if number := request.query_params.get("number"):
        ref = ref.where("number", "==", number)
    if email := request.query_params.get("email"):
        ref = ref.where("email", "==", email)
    results = await ref.get()
    return JSONResponse([EventStudentSchema(request.event).dump_firestore(x) for x in results])


@require_auth(type="admin")
@fetch_event()
async def get_event_student(request: Request):
    id = request.path_params["student_id"]
    result = await db.eventStudent(request.event.id, id).get()
    if not result.exists:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse(EventStudentSchema(request.event).dump_firestore(result))


@require_auth(type="admin")
@fetch_event()
async def update_event_student(request: Request):
    schema = EventStudentSchema(request.event)
    update = schema.load(await request.json())
    ref = db.eventStudent(request.event.id, request.path_params["student_id"])
    if not (await ref.get()).exists:
        return JSONResponse({"error": "Not found"}, status_code=404)
    await ref.set(update, merge=True)
    result = await ref.get()
    return JSONResponse(schema.dump_firestore(result))


@require_auth(type="admin")
@fetch_event()
async def delete_event_student(request: Request):
    await db.eventStudent(request.event.id, request.path_params["student_id"]).delete()
    return Response(status_code=204)


routes = [
    Route("/orgs/", list_event_orgs),
    Route("/orgs/{org_id}", get_event_org),
    Route("/orgs/{org_id}", update_event_org, methods=["PATCH"]),
    Route("/orgs/{org_id}", delete_event_org, methods=["DELETE"]),
    Route("/teams/", list_event_teams),
    Route("/teams/{team_id}", get_event_team),
    Route("/teams/{team_id}", update_event_team, methods=["PATCH"]),
    Route("/teams/{team_id}", delete_event_team, methods=["DELETE"]),
    Route("/students/", list_event_students),
    Route("/students/{student_id}", get_event_student),
    Route("/students/{student_id}", update_event_student, methods=["PATCH"]),
    Route("/students/{student_id}", delete_event_student, methods=["DELETE"]),
]
