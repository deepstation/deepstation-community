import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status, Security
from fastapi.security.api_key import APIKeyHeader

load_dotenv()

API_KEY_NAME = "X-API-Key"
API_KEY = os.getenv("DEEPSTATION_API_KEY")

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