from app import schemas
from app.FakeUser import fUser
from app.crud.base import CRUDBase
from app.database import db
from app.utils.password_hash import get_password_hash


class CRUDUser(CRUDBase):
    async def create(
            self,
            **kwargs
    ):
        schema_in = kwargs.get("schema_in")

        if getattr(schema_in, "password", None) is not None:
            setattr(schema_in, "hashed_password", get_password_hash(getattr(schema_in, "password")))
            setattr(schema_in, "password", None)

        return await super(CRUDUser, self).create(
            **kwargs
        )

    async def update(
            self,
            **kwargs
    ):
        schema_in = kwargs.get("schema_in")

        if getattr(schema_in, "password", None) is not None:
            setattr(schema_in, "hashed_password", get_password_hash(getattr(schema_in, "password")))
            setattr(schema_in, "password", None)

        return await super(CRUDUser, self).update(
            **kwargs
        )

    @staticmethod
    async def get_by_email(**kwargs):
        schema_in = kwargs.get("schema_in", None)

        if schema_in is None:
            return None

        email = getattr(schema_in, "email", None)

        if email is None:
            return None

        user = await db[schema_in.__COLLECTION__].find_one({"email": email})

        if user is None:
            return fUser

        return schemas.UserUpdate(**user)
