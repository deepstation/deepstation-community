from app.models.model import Lead, Client
from typing import Optional

class LeadsRepository:
    @staticmethod
    async def get_client_by_uuid(client_uuid: str) -> Optional[Client]:
        return await Client.get_or_none(uuid=client_uuid)

    @staticmethod
    async def create_lead(name: str, phone_number: str, client_id: int) -> Lead:
        return await Lead.create(
            name=name,
            phone_number=phone_number,
            client_id=client_id
        )
    
    @staticmethod
    async def get_lead_by_email(email: str) -> Optional[Lead]:
        """Get a lead by their email address"""
        return await Lead.get_or_none(email=email)
    
    @staticmethod
    async def create_lead_by_email(email: str, client_id: int) -> Lead:
        """Create a new lead with an email address"""
        return await Lead.create(
            email=email,
            client_id=client_id
        ) 