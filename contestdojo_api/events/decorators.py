import functools
from typing import Any, Awaitable, Callable

from starlette.requests import Request
from starlette.responses import JSONResponse

from ..firebase import db


def fetch_event(path_param="event_id", check_permissions=True):
    def decorator(func: Callable[[Request], Awaitable[Any]]):
        @functools.wraps(func)
        async def wrapped(request: Request):
            id = request.path_params[path_param]
            request.event = await db.event(id).get()
            request.entity = await request.event.to_dict()["owner"].get()

            if check_permissions and not any(
                request.user.uid == x.id for x in request.entity.to_dict()["admins"]
            ):
                return JSONResponse({"error": "Forbidden"}, status_code=403)

            return await func(request)

        return wrapped

    return decorator
