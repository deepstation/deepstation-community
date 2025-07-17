from fastapi import APIRouter, HTTPException, Form
from app.library.emails.email_utils import send_email_response, extract_email_thread_ids_and_set_references_and_in_reply_to_to_message_id, handle_allowed_recipients_and_cc_emails
from app.library.llm_utils import generate_ai_response
from app.prompts.emails.emails_prompt_templates import (
    provide_information_in_email_format_prompt,
)
from app.models.model import Client, Conversation, Lead, CompanyInformation
from app.repository.company_information_repository import CompanyInformationRepository
from app.repository.clients_repository import ClientsRepository
from app.repository.leads_repository import LeadsRepository
from app.prompts.emails.emails_prompt_templates import (
    parse_email_response_for_only_sent_message_prompt,
)
from app.repository.conversations_repository import ConversationsRepository
from app.models.model import MessageType
import json
import logging
from app.library.luma_utils import fetch_luma_events
from app.services.email.email_services import get_client_lead_company_information
from app.services.email.email_community_support_services import community_support_email_service
logger = logging.getLogger(__name__)

emails_router = APIRouter()

@emails_router.post("/api/email/incoming/")
async def handle_email(
    to: str = Form(...),  # Recipient email
    from_email: str = Form(..., alias="from"),  # Sender email with alias for "from"
    subject: str = Form(...),  # Email subject
    text: str = Form(None),  # Plain text email body (optional)
    headers_field: str = Form(None, alias="headers"),
):
    try:
       return await community_support_email_service(to, from_email, subject, text, headers_field)
    except Exception as e:
        print("error: ", e)
        logger.error(f"Error in handle_email: {e}")
        raise HTTPException(status_code=500, detail=str(e))
