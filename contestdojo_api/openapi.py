from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

# --- Helpers ---


def _ref(name):
    return {"$ref": f"#/components/schemas/{name}"}


def _json(schema):
    return {"application/json": {"schema": schema}}


def _list_of(name):
    return {"type": "array", "items": _ref(name)}


def _path_param(name, description=""):
    p = {"name": name, "in": "path", "required": True, "schema": {"type": "string"}}
    if description:
        p["description"] = description
    return p


def _query_param(name, description=""):
    p = {"name": name, "in": "query", "required": False, "schema": {"type": "string"}}
    if description:
        p["description"] = description
    return p


_AUTH_ERRORS = {
    "401": {"description": "Unauthorized", "content": _json(_ref("Error"))},
    "403": {"description": "Forbidden", "content": _json(_ref("Error"))},
}

_NOT_FOUND = {
    "404": {"description": "Not found", "content": _json(_ref("Error"))},
}

_SECURITY = [{"bearerAuth": []}]

_EVENT_ID = _path_param("event_id", "Event ID")


# --- Spec construction ---


def _build_spec() -> APISpec:
    from marshmallow_union import Union as UnionField

    from .schemas import (
        DocumentReference,
        EntitySchema,
        EventAddOnSchema,
        EventCostAdjustmentRuleSchema,
        EventCostAdjustmentSchema,
        EventCustomFieldFlagsSchema,
        EventCustomFieldSchema,
        EventOrganizationSchema,
        EventSchema,
        EventStudentSchema,
        EventTeamSchema,
        OrganizationSchema,
        UserSchema,
    )

    ma_plugin = MarshmallowPlugin()

    spec = APISpec(
        title="ContestDojo API",
        version="0.1.0",
        openapi_version="3.0.3",
        info={"description": "API for the ContestDojo competition management platform."},
        plugins=[ma_plugin],
    )

    # Custom field mappings
    def _custom_fields(converter, field, **kwargs):
        if isinstance(field, DocumentReference):
            return {"type": "string", "description": "Document reference ID"}
        if isinstance(field, UnionField):
            return {"oneOf": [converter.field2property(f) for f in field._candidate_fields]}
        return {}

    ma_plugin.converter.add_attribute_function(_custom_fields)

    # Security scheme
    spec.components.security_scheme(
        "bearerAuth",
        {"type": "http", "scheme": "bearer", "description": "Firebase API token"},
    )

    # Register schemas
    spec.components.schema("User", schema=UserSchema)
    spec.components.schema("Organization", schema=OrganizationSchema)
    spec.components.schema("Entity", schema=EntitySchema)
    spec.components.schema("EventCostAdjustmentRule", schema=EventCostAdjustmentRuleSchema)
    spec.components.schema("EventCostAdjustment", schema=EventCostAdjustmentSchema)
    spec.components.schema("EventCustomFieldFlags", schema=EventCustomFieldFlagsSchema)
    spec.components.schema("EventCustomField", schema=EventCustomFieldSchema)
    spec.components.schema("EventAddOn", schema=EventAddOnSchema)
    spec.components.schema("Event", schema=EventSchema)
    spec.components.schema("EventOrganization", schema=EventOrganizationSchema(event=None))
    spec.components.schema("EventStudent", schema=EventStudentSchema(event=None))
    spec.components.schema("EventTeam", schema=EventTeamSchema(event=None))

    spec.components.schema(
        "Error",
        {"type": "object", "properties": {"error": {"type": "string"}}},
    )
    spec.components.schema(
        "ValidationError",
        {
            "type": "object",
            "properties": {"errors": {"type": "object", "additionalProperties": True}},
        },
    )

    # --- Paths ---

    # Index
    spec.path(
        path="/",
        operations={
            "get": {
                "summary": "Health check",
                "operationId": "index",
                "responses": {
                    "200": {
                        "description": "API is running",
                        "content": _json(
                            {
                                "type": "object",
                                "properties": {"hello": {"type": "string"}},
                            }
                        ),
                    },
                },
            },
        },
    )

    # Entities
    spec.path(
        path="/entities/",
        operations={
            "get": {
                "summary": "List entities",
                "operationId": "listEntities",
                "tags": ["Entities"],
                "security": _SECURITY,
                "responses": {
                    "200": {
                        "description": "List of entities the authenticated admin has access to",
                        "content": _json(_list_of("Entity")),
                    },
                    **_AUTH_ERRORS,
                },
            },
        },
    )

    spec.path(
        path="/entities/{id}",
        operations={
            "get": {
                "summary": "Get entity",
                "operationId": "getEntity",
                "tags": ["Entities"],
                "security": _SECURITY,
                "parameters": [_path_param("id", "Entity ID")],
                "responses": {
                    "200": {
                        "description": "Entity details",
                        "content": _json(_ref("Entity")),
                    },
                    **_AUTH_ERRORS,
                },
            },
        },
    )

    # Events
    spec.path(
        path="/events/",
        operations={
            "get": {
                "summary": "List events",
                "operationId": "listEvents",
                "tags": ["Events"],
                "security": _SECURITY,
                "responses": {
                    "200": {
                        "description": "List of events for entities the admin has access to",
                        "content": _json(_list_of("Event")),
                    },
                    **_AUTH_ERRORS,
                },
            },
        },
    )

    spec.path(
        path="/events/{event_id}",
        operations={
            "get": {
                "summary": "Get event",
                "operationId": "getEvent",
                "tags": ["Events"],
                "security": _SECURITY,
                "parameters": [_EVENT_ID],
                "responses": {
                    "200": {
                        "description": "Event details",
                        "content": _json(_ref("Event")),
                    },
                    **_AUTH_ERRORS,
                },
            },
        },
    )

    # Event Organizations
    spec.path(
        path="/events/{event_id}/orgs/",
        operations={
            "get": {
                "summary": "List event organizations",
                "operationId": "listEventOrgs",
                "tags": ["Event Organizations"],
                "security": _SECURITY,
                "parameters": [_EVENT_ID],
                "responses": {
                    "200": {
                        "description": "List of organizations registered for the event",
                        "content": _json(_list_of("EventOrganization")),
                    },
                    **_AUTH_ERRORS,
                },
            },
        },
    )

    spec.path(
        path="/events/{event_id}/orgs/{org_id}",
        operations={
            "get": {
                "summary": "Get event organization",
                "operationId": "getEventOrg",
                "tags": ["Event Organizations"],
                "security": _SECURITY,
                "parameters": [_EVENT_ID, _path_param("org_id", "Organization ID")],
                "responses": {
                    "200": {
                        "description": "Event organization details",
                        "content": _json(_ref("EventOrganization")),
                    },
                    **_AUTH_ERRORS,
                    **_NOT_FOUND,
                },
            },
            "patch": {
                "summary": "Update event organization",
                "operationId": "updateEventOrg",
                "tags": ["Event Organizations"],
                "security": _SECURITY,
                "parameters": [_EVENT_ID, _path_param("org_id", "Organization ID")],
                "requestBody": {"required": True, "content": _json(_ref("EventOrganization"))},
                "responses": {
                    "200": {
                        "description": "Updated event organization",
                        "content": _json(_ref("EventOrganization")),
                    },
                    "400": {
                        "description": "Validation error",
                        "content": _json(_ref("ValidationError")),
                    },
                    **_AUTH_ERRORS,
                    **_NOT_FOUND,
                },
            },
            "delete": {
                "summary": "Delete event organization",
                "operationId": "deleteEventOrg",
                "tags": ["Event Organizations"],
                "security": _SECURITY,
                "parameters": [_EVENT_ID, _path_param("org_id", "Organization ID")],
                "responses": {
                    "204": {"description": "Deleted"},
                    **_AUTH_ERRORS,
                },
            },
        },
    )

    # Event Teams
    spec.path(
        path="/events/{event_id}/teams/",
        operations={
            "get": {
                "summary": "List event teams",
                "operationId": "listEventTeams",
                "tags": ["Event Teams"],
                "security": _SECURITY,
                "parameters": [
                    _EVENT_ID,
                    _query_param("org", "Filter by organization ID"),
                    _query_param("number", "Filter by team number"),
                ],
                "responses": {
                    "200": {
                        "description": "List of teams for the event",
                        "content": _json(_list_of("EventTeam")),
                    },
                    **_AUTH_ERRORS,
                },
            },
        },
    )

    spec.path(
        path="/events/{event_id}/teams/{team_id}",
        operations={
            "get": {
                "summary": "Get event team",
                "operationId": "getEventTeam",
                "tags": ["Event Teams"],
                "security": _SECURITY,
                "parameters": [_EVENT_ID, _path_param("team_id", "Team ID")],
                "responses": {
                    "200": {
                        "description": "Event team details",
                        "content": _json(_ref("EventTeam")),
                    },
                    **_AUTH_ERRORS,
                    **_NOT_FOUND,
                },
            },
            "patch": {
                "summary": "Update event team",
                "operationId": "updateEventTeam",
                "tags": ["Event Teams"],
                "security": _SECURITY,
                "parameters": [_EVENT_ID, _path_param("team_id", "Team ID")],
                "requestBody": {"required": True, "content": _json(_ref("EventTeam"))},
                "responses": {
                    "200": {
                        "description": "Updated event team",
                        "content": _json(_ref("EventTeam")),
                    },
                    "400": {
                        "description": "Validation error",
                        "content": _json(_ref("ValidationError")),
                    },
                    **_AUTH_ERRORS,
                    **_NOT_FOUND,
                },
            },
            "delete": {
                "summary": "Delete event team",
                "operationId": "deleteEventTeam",
                "tags": ["Event Teams"],
                "security": _SECURITY,
                "parameters": [_EVENT_ID, _path_param("team_id", "Team ID")],
                "responses": {
                    "204": {"description": "Deleted"},
                    **_AUTH_ERRORS,
                },
            },
        },
    )

    # Event Students
    spec.path(
        path="/events/{event_id}/students/",
        operations={
            "get": {
                "summary": "List event students",
                "operationId": "listEventStudents",
                "tags": ["Event Students"],
                "security": _SECURITY,
                "parameters": [
                    _EVENT_ID,
                    _query_param("org", "Filter by organization ID"),
                    _query_param("team", "Filter by team ID"),
                    _query_param("number", "Filter by student number"),
                    _query_param("email", "Filter by email address"),
                ],
                "responses": {
                    "200": {
                        "description": "List of students for the event",
                        "content": _json(_list_of("EventStudent")),
                    },
                    **_AUTH_ERRORS,
                },
            },
        },
    )

    spec.path(
        path="/events/{event_id}/students/{student_id}",
        operations={
            "get": {
                "summary": "Get event student",
                "operationId": "getEventStudent",
                "tags": ["Event Students"],
                "security": _SECURITY,
                "parameters": [_EVENT_ID, _path_param("student_id", "Student ID")],
                "responses": {
                    "200": {
                        "description": "Event student details",
                        "content": _json(_ref("EventStudent")),
                    },
                    **_AUTH_ERRORS,
                    **_NOT_FOUND,
                },
            },
            "patch": {
                "summary": "Update event student",
                "operationId": "updateEventStudent",
                "tags": ["Event Students"],
                "security": _SECURITY,
                "parameters": [_EVENT_ID, _path_param("student_id", "Student ID")],
                "requestBody": {"required": True, "content": _json(_ref("EventStudent"))},
                "responses": {
                    "200": {
                        "description": "Updated event student",
                        "content": _json(_ref("EventStudent")),
                    },
                    "400": {
                        "description": "Validation error",
                        "content": _json(_ref("ValidationError")),
                    },
                    **_AUTH_ERRORS,
                    **_NOT_FOUND,
                },
            },
            "delete": {
                "summary": "Delete event student",
                "operationId": "deleteEventStudent",
                "tags": ["Event Students"],
                "security": _SECURITY,
                "parameters": [_EVENT_ID, _path_param("student_id", "Student ID")],
                "responses": {
                    "204": {"description": "Deleted"},
                    **_AUTH_ERRORS,
                },
            },
        },
    )

    return spec


_spec_dict = None


def get_spec() -> dict:
    global _spec_dict
    if _spec_dict is None:
        _spec_dict = _build_spec().to_dict()
    return _spec_dict


# --- Route handlers ---


async def openapi_json(request: Request):
    return JSONResponse(get_spec())


async def swagger_ui(request: Request):
    html = """\
<!DOCTYPE html>
<html>
<head>
    <title>ContestDojo API</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>SwaggerUIBundle({url: '/openapi.json', dom_id: '#swagger-ui'});</script>
</body>
</html>"""
    return HTMLResponse(html)


async def redoc_ui(request: Request):
    html = """\
<!DOCTYPE html>
<html>
<head>
    <title>ContestDojo API</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
    <redoc spec-url='/openapi.json'></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
</body>
</html>"""
    return HTMLResponse(html)


routes = [
    Route("/openapi.json", openapi_json),
    Route("/docs", swagger_ui),
    Route("/redoc", redoc_ui),
]
