import os
from datetime import datetime, timedelta

from jose import jwt

from app import schemas
from app.crud import crud_user
from app.utils.password_hash import verify_password

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 2
ACCESS_TOKEN_EXPIRE_MINUTES_DEFAULT = 15

SECRET_KEY = os.environ["SECRET_KEY"]


async def authenticate_user(email: str, password: str):
    schema_in = schemas.UserUpdate(email=email)
    user = await crud_user.get_by_email(schema_in=schema_in)

    if user is None:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES_DEFAULT)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
