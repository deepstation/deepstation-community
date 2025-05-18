from app.models.model import Lead, Client
from typing import Optional

class LeadsRepository:
    @staticmethod
    async def get_client_by_uuid(client_uuid: str) -> Optional[Client]:
        return await Client.get_or_none(uuid=client_uuid)

    @staticmethod
    async def create_lead(name: str, ai_phone_number: str, client_id: int) -> Lead:
        return await Lead.create(
            name=name,
            ai_phone_number=ai_phone_number,
            client_id=client_id
        ) 