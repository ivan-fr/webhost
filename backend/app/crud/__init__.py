import app.crud.user as crud_user
from app import schemas
from app.crud.base import CRUDBase

crud_user = crud_user.CRUDUser(
    user_id_field="_id",
    collection=getattr(schemas.UserCreate, "__COLLECTION__"),
    mto=getattr(schemas.UserCreate, "__MTO__", {})
)
