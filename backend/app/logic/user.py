import re

from pydantic import BaseModel


class UserFilter(BaseModel):
    nickname: str | None


def sanitize_get_request(schema_in: UserFilter):
    kwargs = {}

    if schema_in.nickname is not None:
        kwargs["query"] = {
            "nickname": {
                "$regex": f"^{schema_in.nickname}$", "$options": "i"
            }
        }

    return kwargs
