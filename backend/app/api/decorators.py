from functools import wraps

from fastapi import HTTPException
from starlette import status

from app.rights import check_rights, get_required_rights


def adapt_api_locals(dict_: dict):
    return dict_.get("kwargs", {})


def basic_controls(controls, mode="", check_user=True):
    def inner(func):
        @wraps(func)
        async def wrapper(**kwargs):
            schema_in = kwargs.get("schema_in", {})

            if kwargs.get("schema_in", None) is not None and not isinstance(kwargs.get("schema_in"), dict):
                schema_in = kwargs.get("schema_in").dict(exclude_unset=True)

            if kwargs.get("for_admin", False):
                required_rights = get_required_rights(kwargs.get("request"), mode)
                if check_rights(kwargs.get("current_user").rights, required_rights):
                    return await func(**kwargs)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="admin requirements are not satisfy",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            if check_user:
                controls.check_current_user(mode=mode, **adapt_api_locals(locals()))

            return await func(**kwargs)

        return wrapper

    return inner


def transformer_method_data_controls(controls, mode=""):
    def inner(func):
        @wraps(func)
        async def wrapper(**kwargs):
            schema_in = kwargs.get("schema_in", {})

            if kwargs.get("schema_in", None) is not None and not isinstance(kwargs.get("schema_in"), dict):
                schema_in = kwargs.get("schema_in").dict(exclude_unset=True)

            data_before_transformation = await controls.api.crud_.get(
                mode="get_one",
                query={"_id": str(schema_in.get("id", None))}
            )

            kwargs["data_before_transformation"] = data_before_transformation

            if mode == "create":
                boolean = await controls.can_i_do(
                    mode=mode,
                    clean_user_depends=True, accept_zero_depends=True,
                    **adapt_api_locals(locals())
                )
            else:
                boolean = await controls.can_i_do(
                    mode=mode,
                    **adapt_api_locals(locals())
                )

            if boolean:
                del kwargs["data_before_transformation"]
                return await func(**kwargs)

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="depends requirements are not satisfy",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return wrapper

    return inner
