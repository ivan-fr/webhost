import pymongo.errors
from fastapi import UploadFile, Request, HTTPException, Depends
from starlette import status
from starlette.responses import Response

from app import schemas
from app.api.controls import Controls
from app.api.decorators import basic_controls, transformer_method_data_controls
from app.api.depends import get_current_user_no_raise


class RouteInit:
    def __init__(self, api):
        controls = Controls(api)

        @api.router.put(f"/{api.singular}", response_model=api.native_schema,
                        response_model_exclude=api.response_model_exclude)
        @basic_controls(controls=controls, mode="update")
        @transformer_method_data_controls(controls=controls, mode="update")
        async def update(
                request: Request,
                schema_in: api.update_schema,
                file: UploadFile | None = None,
                for_admin: int = 0,
                current_user: schemas.UserUpdate = Depends(get_current_user_no_raise)
        ):
            res = None

            try:
                if file is None:
                    res = await api.crud_.update(**locals())

                if await controls.image_process(**locals()):
                    res = await api.crud_.update(**locals())
            except pymongo.errors.DuplicateKeyError:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

            if res is None:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

            return res

        @api.router.delete(f"/{api.singular}")
        @basic_controls(controls, mode="delete")
        @transformer_method_data_controls(controls, mode="delete")
        async def delete(
                request: Request,
                schema_in: api.update_schema,
                for_admin: int = 0,
                current_user: schemas.UserUpdate = Depends(get_current_user_no_raise)
        ):
            if await api.crud_.delete(**locals()):
                return Response(status_code=status.HTTP_204_NO_CONTENT)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        @api.router.post(f"/{api.singular}", response_model=api.native_schema,
                         response_model_exclude=api.response_model_exclude)
        @basic_controls(controls, mode="create", check_user=api.singular != "user")
        @transformer_method_data_controls(controls, mode="create")
        async def create(
                request: Request,
                schema_in: api.native_schema,
                file: UploadFile | None = None,
                for_admin: int = 0,
                current_user: schemas.UserUpdate = Depends(get_current_user_no_raise)
        ):
            try:
                if file is None:
                    return await api.crud_.create(**locals())

                if await controls.image_process(**locals()):
                    return await api.crud_.create(**locals())
            except pymongo.errors.DuplicateKeyError:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        @api.router.post(f"/{api.plural}/filters/own", response_model=list[api.native_schema],
                         response_model_exclude=api.response_model_exclude)
        @basic_controls(controls, mode="get_multi_filters_own")
        async def get_multi_filters_own(
                request: Request,
                schema_in: api.getter_schema | None,
                skip: int = 0,
                limit: int = 100,
                for_admin: int = 0,
                current_user: schemas.UserUpdate = Depends(get_current_user_no_raise)
        ):
            mode = "get_multi_filters_own"
            res = await api.crud_.get(**api.getter_sanitize(schema_in), **locals())

            if len(res):
                return res

            return Response(status_code=status.HTTP_404_NOT_FOUND)

        @api.router.post(f"/{api.plural}/filters", response_model=list[api.native_schema],
                         response_model_exclude=api.response_model_exclude)
        @basic_controls(controls, mode="get_multi_filters")
        async def get_multi_filters(
                request: Request,
                schema_in: api.getter_schema | None,
                skip: int = 0,
                limit: int = 100,
                for_admin: int = 0,
                current_user: schemas.UserUpdate = Depends(get_current_user_no_raise)
        ):
            mode = "get_multi_filters"
            res = await api.crud_.get(**api.getter_sanitize(schema_in), **locals())

            if len(res):
                return res

            return Response(status_code=status.HTTP_404_NOT_FOUND)

        @api.router.post(f"/{api.plural}/exists")
        @basic_controls(controls, mode="get_exists_filters")
        async def get_exists_filters(
                request: Request,
                schema_in: api.getter_schema | None,
                for_admin: int = 0,
                current_user: schemas.UserUpdate = Depends(get_current_user_no_raise)
        ):
            mode = "get_exists_filters"
            res = await api.crud_.get(**api.getter_sanitize(schema_in), **locals())

            if res:
                return Response(status_code=status.HTTP_204_NO_CONTENT)

            return Response(status_code=status.HTTP_404_NOT_FOUND)
