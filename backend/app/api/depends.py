from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from starlette import status

from app import schemas
from app.FakeUser import fUser
from app.crud import crud_user
from app.security import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
oauth2_scheme_no_error = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

credentials_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user_no_raise(
        token: str | None = Depends(oauth2_scheme_no_error)
):
    if token is None:
        return fUser

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub", "")
        if email == "" or email is None:
            return fUser

        token_data = schemas.TokenData(email=email)
    except JWTError:
        return fUser

    schema_in = schemas.UserUpdate(email=token_data.email)
    user = await crud_user.get_by_email(schema_in=schema_in)

    return user
