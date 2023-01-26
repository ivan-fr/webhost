import logging
import os

from dotenv import load_dotenv

from app import base_dir

load_dotenv(os.path.join(base_dir, ".env"))
logging.info(msg=".env loaded")

from fastapi import FastAPI
from pydantic import BaseSettings
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from app.api.router import router
from multiprocessing import Lock

mutex = Lock()


class Settings(BaseSettings):
    openapi_url: str = "/openapi.json"


settings = Settings()

app = FastAPI(openapi_url=settings.openapi_url)
app.add_middleware(GZipMiddleware, minimum_size=1000)

IMAGE_DIR = "images"

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount("/static", StaticFiles(directory=os.path.join(base_dir, IMAGE_DIR)), name="static")
app.include_router(router)
