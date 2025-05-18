from app.models.model import Campaign, Lead, Conversation
from typing import List, Optional

class CampaignsRepository:
    @staticmethod
    async def create_campaign(**kwargs) -> Campaign:
        return await Campaign.create(**kwargs)

    @staticmethod
    async def get_campaign_by_uuid(campaign_uuid: str) -> Optional[Campaign]:
        return await Campaign.get_or_none(uuid=campaign_uuid)

    @staticmethod
    async def list_campaigns(client_id: Optional[int] = None) -> List[Campaign]:
        if client_id:
            return await Campaign.filter(client_id=client_id).all()
        return await Campaign.all()

    @staticmethod
    async def update_campaign(campaign: Campaign, **kwargs) -> Campaign:
        for key, value in kwargs.items():
            setattr(campaign, key, value)
        await campaign.save()
        return campaign

    @staticmethod
    async def add_leads_to_campaign(campaign: Campaign, leads: List[Lead]):
        await campaign.leads.add(*leads)

    @staticmethod
    async def remove_leads_from_campaign(campaign: Campaign, leads: List[Lead]):
        await campaign.leads.remove(*leads)

    @staticmethod
    async def list_leads_in_campaign(campaign: Campaign) -> List[Lead]:
        return await campaign.leads.all()

    @staticmethod
    async def list_conversations_for_campaign(campaign: Campaign) -> List[Conversation]:
        return await Conversation.filter(campaign=campaign).all() 