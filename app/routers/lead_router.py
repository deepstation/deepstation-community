from fastapi import APIRouter
from app.models.model import Lead, Client
import pydantic

lead_router = APIRouter()

class CreateLeadRequest(pydantic.BaseModel):
    name: str
    ai_phone_number: str
    client_uuid: str

@lead_router.post("/api/lead/create")
async def create_lead(
    request: CreateLeadRequest
):
    try:
        client = await Client.get(uuid=request.client_uuid)

        if not client:
            return {"message": "Client not found"}

        lead = await Lead.create(
            name=request.name,
            ai_phone_number=request.ai_phone_number,
            client_id=client.id
    )
        return {"message": "Lead created successfully", "lead_uuid": lead.uuid}
    except Exception as error:
        return {"message": "Error creating lead", "error": str(error)}
