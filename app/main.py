from fastapi import FastAPI
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise
from app.config import TORTOISE_ORM
from app.routers.lead_router import lead_router
from app.routers.sms_router import sms_router
from app.routers.client_router import client_router
from app.routers.campaigns_router import campaigns_router
import os

ENV = os.getenv("ENV")

app = FastAPI(
    title="DeepStation API",
    docs_url=None if ENV != "dev" else "/docs",
    redoc_url=None if ENV != "dev" else "/redoc",
    openapi_url=None if ENV != "dev" else "/openapi.json",
)

register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,
    add_exception_handlers=True,
)

app.include_router(sms_router)
app.include_router(client_router)
app.include_router(lead_router)
app.include_router(campaigns_router)