from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from app.repository.campaigns_repository import CampaignsRepository
from app.models.model import Client, Campaign, Lead
import logging

campaigns_router = APIRouter()
logger = logging.getLogger(__name__)

class CampaignCreateRequest(BaseModel):
    client_uuid: str
    name: str
    description: Optional[str] = None
    status: Optional[str] = "active"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    message_template: Optional[str] = None

class CampaignUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    message_template: Optional[str] = None

class LeadIdsRequest(BaseModel):
    lead_ids: List[int]

@campaigns_router.post("/api/campaigns/", response_model=dict)
async def create_campaign(request: CampaignCreateRequest):
    try:
        client = await Client.get(uuid=request.client_uuid)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        campaign_data = request.dict(exclude={"client_uuid"})
        campaign_data["client"] = client

        campaign = await CampaignsRepository.create_campaign(**campaign_data)
        return {"campaign_uuid": str(campaign.uuid)}
    except Exception as e:
        logger.error(f"Error creating campaign: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create campaign.")

@campaigns_router.get("/api/campaigns/", response_model=List[dict])
async def list_campaigns(client_id: Optional[int] = None):
    try:
        campaigns = await CampaignsRepository.list_campaigns(client_id)
        return [{"uuid": str(c.uuid), "name": c.name, "status": c.status} for c in campaigns]
    except Exception as e:
        logger.error(f"Error listing campaigns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list campaigns.")

@campaigns_router.get("/api/campaigns/{uuid}", response_model=dict)
async def get_campaign(uuid: str):
    try:
        campaign = await CampaignsRepository.get_campaign_by_uuid(uuid)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return {"uuid": str(campaign.uuid), "name": campaign.name, "status": campaign.status, "description": campaign.description}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get campaign.")

@campaigns_router.patch("/api/campaigns/{uuid}", response_model=dict)
async def update_campaign(uuid: str, request: CampaignUpdateRequest):
    try:
        campaign = await CampaignsRepository.get_campaign_by_uuid(uuid)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        updated = await CampaignsRepository.update_campaign(campaign, **{k: v for k, v in request.dict().items() if v is not None})
        return {"uuid": str(updated.uuid), "name": updated.name, "status": updated.status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating campaign: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update campaign.")

@campaigns_router.post("/api/campaigns/{uuid}/add_leads", response_model=dict)
async def add_leads_to_campaign(uuid: str, request: LeadIdsRequest):
    try:
        campaign = await CampaignsRepository.get_campaign_by_uuid(uuid)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        leads = await Lead.filter(id__in=request.lead_ids).all()
        await CampaignsRepository.add_leads_to_campaign(campaign, leads)
        return {"added": [lead.id for lead in leads]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding leads to campaign: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to add leads to campaign.")

@campaigns_router.post("/api/campaigns/{uuid}/remove_leads", response_model=dict)
async def remove_leads_from_campaign(uuid: str, request: LeadIdsRequest):
    try:
        campaign = await CampaignsRepository.get_campaign_by_uuid(uuid)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        leads = await Lead.filter(id__in=request.lead_ids).all()
        await CampaignsRepository.remove_leads_from_campaign(campaign, leads)
        return {"removed": [lead.id for lead in leads]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing leads from campaign: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to remove leads from campaign.")

@campaigns_router.get("/api/campaigns/{uuid}/leads", response_model=List[dict])
async def list_leads_in_campaign(uuid: str):
    try:
        campaign = await CampaignsRepository.get_campaign_by_uuid(uuid)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        leads = await CampaignsRepository.list_leads_in_campaign(campaign)
        return [{"id": lead.id, "name": lead.name, "phone": lead.ai_phone_number} for lead in leads]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing leads in campaign: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list leads in campaign.")

@campaigns_router.get("/api/campaigns/{uuid}/conversations", response_model=List[dict])
async def list_conversations_for_campaign(uuid: str):
    try:
        campaign = await CampaignsRepository.get_campaign_by_uuid(uuid)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        conversations = await CampaignsRepository.list_conversations_for_campaign(campaign)
        return [{"id": c.id, "uuid": str(c.uuid), "lead_id": c.lead_id} for c in conversations]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing conversations for campaign: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list conversations for campaign.")

# Placeholder for campaign blast endpoint
@campaigns_router.post("/api/campaigns/{uuid}/blast", response_model=dict)
async def blast_campaign(uuid: str):
    try:
        # Implement SMS blast logic here
        return {"message": "Blast triggered (not yet implemented)"}
    except Exception as e:
        logger.error(f"Error blasting campaign: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to trigger campaign blast.") 