import json
from datetime import datetime
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class ModelInMixin(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_to_json

    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return cls(**value)


class DateFieldMixin(BaseModel):
    created_on: Optional[datetime]
    updated_on: Optional[datetime]


class UserCreate(ModelInMixin, DateFieldMixin, BaseModel):
    __COLLECTION__ = "users"
    nickname: str = Field(min_length=4, max_length=100)
    email: EmailStr
    hashed_password: str | None  # fill by system
    password: str | None
    rights: int | None
    last_connection: datetime | None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda dt: dt.isoformat()}


class UserUpdate(ModelInMixin, DateFieldMixin, BaseModel):
    __COLLECTION__ = "users"

    nickname: str | None = Field(min_length=4, max_length=100)
    email: EmailStr | None = None
    hashed_password: str | None  # fill by system
    password: str | None
    rights: int | None
    last_connection: datetime | None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda dt: dt.isoformat()}


class UserOut(DateFieldMixin, BaseModel):
    nickname: str | None = Field(min_length=4, max_length=100)
    last_connection: datetime | None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda dt: dt.isoformat()}


class UserFieldMixin(BaseModel):
    created_by_id: PyObjectId | None
    updated_by_id: PyObjectId | None

    created_by: UserOut | None
    updated_by: UserOut | None

    __MTO__ = {
        "created_by": {
            "from": UserCreate.__COLLECTION__,
            "localField": "created_by_id",
            "foreignField": "_id"
        },
        "updated_by": {
            "from": UserCreate.__COLLECTION__,
            "localField": "updated_by_id",
            "foreignField": "_id"
        }
    }


class ArticleCreate(ModelInMixin, UserFieldMixin, DateFieldMixin, BaseModel):
    __COLLECTION__ = "articles"

    title: str = Field(max_length=100)
    description: str | None
    referral_link_id: PyObjectId | None
    bonus: str | None
    bonus_conditions: str | None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda dt: dt.isoformat()}


class ArticleUpdate(ModelInMixin, UserFieldMixin, DateFieldMixin, BaseModel):
    __COLLECTION__ = "articles"

    title: str | None = Field(max_length=100)
    description: str | None
    flag_id: PyObjectId | None
    menu_id: PyObjectId | None
    bonus: str | None
    bonus_conditions: str | None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda dt: dt.isoformat()}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str


UserCreate.update_forward_refs()
UserUpdate.update_forward_refs()
ArticleCreate.update_forward_refs()
ArticleUpdate.update_forward_refs()
