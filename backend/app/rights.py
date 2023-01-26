from fastapi import HTTPException
from fastapi import Request
from starlette import status

CAN_READ = 1 << 0
CAN_UPDATE = 1 << 1
CAN_DELETE = 1 << 2
CAN_CREATE = 1 << 3

SWITCH = {
    CAN_DELETE: True,
    CAN_UPDATE: True,
    CAN_READ: True,
    CAN_CREATE: True
}

authorization_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="You don't have rights",
    headers={"WWW-Authenticate": "Bearer"},
)


def check_rights(my_rights, rights: list):
    if my_rights is None:
        return False

    return all(check_right(my_rights, right) for right in rights)


def check_right(my_rights, right):
    if not SWITCH.get(right, False):
        raise authorization_exception

    return my_rights & right == right


def get_required_rights(request: Request, mode: str):
    required_rights = []

    if request.method.lower() == "post" and mode.startswith("get_"):
        required_rights.append(CAN_READ)
    elif request.method.lower() == "post" and mode == "create":
        required_rights.append(CAN_CREATE)
    elif request.method.lower() == "put" and mode == "update":
        required_rights.append(CAN_UPDATE)
    elif request.method.lower() == "delete":
        required_rights.append(CAN_DELETE)

    if len(required_rights) == 0:
        raise authorization_exception

    return required_rights
