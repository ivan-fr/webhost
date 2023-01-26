import asyncio
import getopt
import logging
import os
import sys

from dotenv import load_dotenv

from app import base_dir

load_dotenv(os.path.join(base_dir, ".env"))
logging.info(msg=".env loaded")

from app.crud import crud_user
from app.schemas import UserUpdate

from app.rights import CAN_UPDATE, CAN_READ, CAN_CREATE, CAN_DELETE

switch = {
    "update": CAN_UPDATE,
    "create": CAN_CREATE,
    "read": CAN_READ,
    "delete": CAN_DELETE,
}


async def running(_id__, _rights_):
    e_rights = 0
    for r in _rights_:
        e_rights |= r

    user_update = UserUpdate(_id=_id__, rights=e_rights)
    await crud_user.update(schema_in=user_update)


if __name__ == '__main__':
    text = 'change_rights -i <id_user> -r <rights> (for example => update,create,read,delete) -a <all_rights>'
    argumentList = sys.argv[1:]
    try:
        opts, args = getopt.getopt(argumentList, "hi:r:a", ["id_user=", "rights=", "all_rights="])
    except getopt.GetoptError:
        raise Exception(text)

    id_ = None
    rights_ = None
    for opt, arg in opts:
        if opt == "-h":
            print(text)
            sys.exit()
        if opt == "-i":
            id_ = arg
        elif opt == "-r":
            rights_ = arg
        elif opt == "-a":
            rights_ = "update,create,read,delete"
        else:
            raise Exception(text)

    if id_ is None:
        raise Exception(text)

    rights_ = rights_.split(",")
    effective_rights = []

    for right in rights_:
        effective_rights.append(switch.get(right, 0))

    try:
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except AttributeError:
            pass
        asyncio.run(running(id_, effective_rights))
    except RuntimeError:
        pass

    print("Done")
