from datetime import datetime

from fastapi.encoders import jsonable_encoder

from app.FakeUser import fUser, FakeUser
from app.database import db


class CRUDBase:
    def __init__(
            self,
            id_attr: str = "id",
            user_id_field=None,
            collection="",
            mto=None
    ):
        self.user_id_field = user_id_field
        self.id_attr = id_attr
        self.__COLLECTION__ = collection
        self.__MTO__ = mto or {}

    async def get(
            self,
            **kwargs
    ):
        mode = kwargs.get("mode", None)
        limit = min(kwargs.get("limit", 100), 100)
        skip = kwargs.get("skip", 0) or 0
        query = kwargs.get("query", {}) or {}
        mto = kwargs.get("mto", []) or []
        sort = kwargs.get("sort", {}) or {}
        group = kwargs.get("group", {}) or {}

        aggregate = []

        if mode == "get_multi_filters_own":
            if self.user_id_field is None:
                return []

            current_user = kwargs.get("current_user", fUser)

            if current_user.id is None:
                return []

            query.update({self.user_id_field: str(current_user.id)})

        if len(mto) > 0:
            for a_mto in set(mto):
                if self.__MTO__.get(a_mto, None) is None:
                    continue

                mto_description = self.__MTO__[a_mto].copy()
                mto_description["as"] = a_mto

                aggregate.append({
                    "$lookup": mto_description
                })

                aggregate.append({
                    "$unwind": f"${a_mto}"
                })

        if len(group) > 0:
            aggregate.append({
                "group": group
            })

        if len(aggregate) > 0:
            if len(query) > 0:
                aggregate.append({"$match": query})

            if len(sort) > 0:
                aggregate.append({"$sort": sort})

            if mode == "get_exists_filters" or mode == "get_one":
                aggregate.append({"$limit": 1})
            else:
                aggregate.append({"$limit": limit})

            aggregate.append({"$skip": skip})

        if mode == "get_exists_filters" or mode == "get_one":
            if len(aggregate) > 0:
                cursor = db[self.__COLLECTION__].aggregate(aggregate)
                return await cursor.next()
            else:
                return await db[self.__COLLECTION__].find_one(query)
        else:
            if len(aggregate) > 0:
                cursor = db[self.__COLLECTION__].aggregate(aggregate)
            else:
                cursor = db[self.__COLLECTION__].find(query)

                for field, direction in sort.items():
                    cursor.sort(field, direction)

                cursor = cursor.limit(limit).skip(skip)

        return await cursor.to_list(length=None)

    async def create(
            self,
            **kwargs
    ):
        schema_in = kwargs.get("schema_in", None)
        current_user = kwargs.get("current_user", fUser)

        if hasattr(schema_in, "created_by_id") and not isinstance(kwargs.get("current_user", fUser), FakeUser):
            setattr(schema_in, "created_by_id", current_user.id)

        if hasattr(schema_in, "created_on"):
            setattr(schema_in, "created_on", datetime.now())

        json_schema = jsonable_encoder(schema_in)
        newer = await db[self.__COLLECTION__].insert_one(json_schema)
        created = await db[self.__COLLECTION__].find_one({"_id": newer.inserted_id})

        return created

    async def update(
            self,
            **kwargs
    ):
        schema_in = kwargs.get("schema_in")
        current_user = kwargs.get("current_user", fUser)

        if hasattr(schema_in, "updated_by_id") and not isinstance(kwargs.get("current_user", fUser), FakeUser):
            setattr(schema_in, "updated_by_id", current_user.id)

        if hasattr(schema_in, "updated_on"):
            setattr(schema_in, "updated_on", datetime.now())

        schema_dict = schema_in.dict(exclude_unset=True)

        if len(schema_dict) >= 1:
            update_result = await db[self.__COLLECTION__].update_one(
                {"_id": str(schema_dict.get(self.id_attr))},
                {"$set": schema_dict}
            )

            if update_result.modified_count == 1:
                if (
                        updated := await db[self.__COLLECTION__].find_one(
                            {"_id": str(schema_dict.get(self.id_attr))}
                        )
                ) is not None:
                    return updated

        return None

    async def delete(self, **kwargs):
        schema_in = kwargs.get("schema_in")
        delete_result = await db[self.__COLLECTION__].delete_one({"_id": str(getattr(schema_in, self.id_attr))})

        if delete_result.deleted_count == 1:
            return True

        return False
