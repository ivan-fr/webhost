from datetime import timedelta, datetime

from fastapi import APIRouter, Body
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from starlette.responses import JSONResponse, Response

from app import schemas
from app.FakeUser import FakeUser
from app.api.common import router as common_router
from app.api.depends import get_current_user_no_raise
from app.crud import crud_user
from app.crud.user import CRUDUser
from app.security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, authenticate_user
from app.utils.mail import generate_password_reset_token, send_reset_password_email, verify_password_reset_token
from app.utils.password_hash import get_password_hash

router = APIRouter()


@router.post("/password-recovery")
async def recover_password(email: EmailStr = Body(..., embed=True)):
    """
    Password Recovery
    """
    schema_in = schemas.UserUpdate(email=email)
    user = await CRUDUser.get_by_email(schema_in=schema_in)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=user.email)
    await send_reset_password_email(
        email_to=user.email, token=password_reset_token
    )

    return JSONResponse(status_code=200, content={"message": "email has been sent"})


@router.post("/reset-password")
async def reset_password(
        token: str = Body(...),
        new_password: str = Body(...),
):
    """
    Reset password
    """
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")

    schema_in = schemas.UserUpdate(email=email)
    user = await CRUDUser.get_by_email(schema_in=schema_in)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this email does not exist in the system.",
        )

    hashed_password = get_password_hash(new_password)
    user.hashed_password = hashed_password

    return Response(status_code=status.HTTP_200_OK)


@router.post("/token", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "sub_wallet": ""}, expires_delta=access_token_expires
    )

    user.last_connection = datetime.now()
    await crud_user.update(schema_in=user)

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=schemas.UserCreate)
async def read_users_me(current_user: schemas.UserUpdate | FakeUser = Depends(get_current_user_no_raise)):
    if current_user.id is None:
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    return current_user


router.include_router(common_router)
