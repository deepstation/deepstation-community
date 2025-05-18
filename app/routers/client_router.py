from fastapi import APIRouter
from app.models.model import Client
import pydantic

class CreateClientRequest(pydantic.BaseModel):
    name: str
    ai_phone_number: str
    ai_bot_name: str

client_router = APIRouter()

@client_router.post("/api/client/create")
async def create_client(
    request: CreateClientRequest
):
    try:
        client = await Client.create(
            name=request.name,
            ai_phone_number=request.ai_phone_number,
            ai_bot_name=request.ai_bot_name
        )

        return {"message": "Client created successfully", "client_uuid": client.uuid}
    except Exception as e:
        return {"message": "Client creation failed", "error": str(e)}
