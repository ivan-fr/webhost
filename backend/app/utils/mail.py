import os
from datetime import timedelta, datetime

from fastapi import HTTPException
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from fastapi_mail.errors import ConnectionErrors
from jose import jwt
from pydantic import EmailStr
from starlette import status

from app import base_dir

mail_conf = ConnectionConfig(
    MAIL_USERNAME=os.environ["SMTP_USER"],
    MAIL_PASSWORD=os.environ["SMTP_PASSWORD"],
    MAIL_FROM=os.environ["EMAILS_FROM_EMAIL"],
    MAIL_PORT=int(os.environ["SMTP_PORT"]),
    MAIL_SERVER=os.environ["SMTP_HOST"],
    MAIL_FROM_NAME=os.environ["EMAILS_FROM_NAME"],
    MAIL_SSL_TLS=True if (os.environ["SMTP_SSL"] == "True" or os.environ["SMTP_TLS"] == "True") else False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=os.path.join(base_dir, "templates", "build"),
    MAIL_STARTTLS=False
)

fm = FastMail(mail_conf)


def generate_password_reset_token(email: EmailStr) -> str:
    delta = timedelta(hours=int(os.environ["EMAIL_RESET_TOKEN_EXPIRE_HOURS"]))
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email}, os.environ["SECRET_KEY"], algorithm="HS256"
    )
    return encoded_jwt


def verify_password_reset_token(token: str):
    try:
        decoded_token = jwt.decode(token, os.environ["SECRET_KEY"], algorithms=["HS256"])
        return decoded_token["sub"]
    except jwt.JWTError:
        return None


async def send_email(
        recipients: list[str],
        template_name: str,
        subject_template: str = "",
        template_context=None
):
    if template_context is None:
        template_context = {}

    message = MessageSchema(
        subject=subject_template,
        recipients=recipients,
        template_body=template_context,
        subtype=MessageType.html
    )

    try:
        await fm.send_message(message, template_name=template_name)
    except ConnectionErrors:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


async def send_reset_password_email(email_to: str, token: str) -> None:
    project_name = os.environ["EMAILS_FROM_NAME"]
    subject = f"{project_name} - Password recovery for user {email_to}"

    server_host = os.environ["SERVER_HOST"]
    link = f"{server_host}/?reset_password=1&token={token}"

    await send_email(
        recipients=[email_to],
        subject_template=subject,
        template_context={
            "project_name": project_name,
            "username": email_to,
            "email": email_to,
            "valid_hours": int(os.environ["EMAIL_RESET_TOKEN_EXPIRE_HOURS"]),
            "link": link,
        },
        template_name="reset_password.html"
    )
