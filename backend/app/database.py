import os

import motor.motor_asyncio

client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["DATABASE_URL"])
db = getattr(client, os.environ["DATABASE_NAME"])
