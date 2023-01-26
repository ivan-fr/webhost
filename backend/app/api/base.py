import pymongo
from fastapi import APIRouter
from pydantic import BaseModel

from app import crud
from app.api.default_route import RouteInit
from app.database import db


class APIBase:
    def __init__(
            self,
            native_schema,
            update_schema,
            singular,
            plural,
            router: APIRouter,
            crud_=None,
            actions_super_user=None,
            depends=None,
            user_id_field="created_by_id",
            response_model_exclude=None,
            unique_index: set = None,
            getter_schema=BaseModel,
            getter_sanitize=None
    ):
        self.native_schema = native_schema
        self.update_schema = update_schema
        self.singular = singular
        self.plural = plural

        self.initial_router = router
        self.router = APIRouter(prefix="/admin/{for_admin}")

        self.user_id_field = user_id_field
        collection = getattr(native_schema, "__COLLECTION__") or getattr(
            update_schema, "__COLLECTION__"
        )

        if unique_index is not None:
            indexes = ((u_i, pymongo.ASCENDING) for u_i in unique_index)
            db[collection].create_index(list(indexes), unique=True)

        if actions_super_user is None:
            self.actions_super_user = []
        else:
            self.actions_super_user = actions_super_user

        if response_model_exclude is None:
            self.response_model_exclude = {}
        else:
            self.response_model_exclude = response_model_exclude

        self.getter_schema = getter_schema
        self.getter_sanitize = getter_sanitize

        if getter_sanitize is None:
            self.getter_sanitize = lambda s: {}

        if depends is None:
            self.depends = {}
        else:
            self.depends = depends

        if crud_ is None:
            self.crud_ = crud.CRUDBase(
                user_id_field=user_id_field,
                collection=collection,
                mto=getattr(native_schema, "__MTO__", {})
            )
        else:
            self.crud_ = crud_

        if depends is not None:
            for a_crud, meta in depends.items():
                if a_crud == "self":
                    depends[self.crud_] = meta
                    break

            try:
                del depends["self"]
            except KeyError:
                pass

        self.init_routes()

    def init_routes(self):
        RouteInit(self)
        self.initial_router.include_router(self.router)
