from fastapi import FastAPI
from fastapi.params import Header
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise
from app.config import TORTOISE_ORM
from app.routers.lead_router import lead_router
from app.routers.sms_router import sms_router
from app.routers.client_router import client_router
from app.routers.campaigns_router import campaigns_router
import os
from fastapi.security.api_key import APIKeyHeader

from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader


API_KEY_NAME = "X-API-Key"
API_KEY = os.getenv("DEEPSTATION_API_KEY")
ENV = os.getenv("ENV")
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key",
        )
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )
    return api_key


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