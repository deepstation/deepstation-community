from app.models.model import Client, Lead, CompanyInformation, Conversation, MessageType, Message
from app.repository.clients_repository import ClientsRepository
from app.repository.leads_repository import LeadsRepository
from app.repository.company_information_repository import CompanyInformationRepository
from app.repository.conversations_repository import ConversationsRepository
from fastapi import HTTPException
import json
from app.prompts.emails.emails_prompt_templates import parse_email_response_for_only_sent_message_prompt
from app.library.llms import chat_completion_request

async def process_email_for_user_message(text: str) -> str:
    
    # If conversation, save the sent message.
    ## 1. Parse the email and get the most recent message
    parsed_emailfor_first_message_prompt = (
        parse_email_response_for_only_sent_message_prompt(text)
    )

    parsed_email_for_user_message = await chat_completion_request(
        [{"role": "user", "content": parsed_emailfor_first_message_prompt}],
        model="gpt-4o",
    )

    if parsed_email_for_user_message is None:
        raise HTTPException(status_code=500, detail="Failed to parse email content")

    return parsed_email_for_user_message

async def get_client_lead_company_information(allowed_recipient: str, email_thread_ids: dict, from_email: str, text: str) -> tuple[Client, Lead, CompanyInformation, Conversation, list[Message], ConversationsRepository, dict, str]:
    # Get Client Information
    client = await Client.filter(ai_email=allowed_recipient).get_or_none()

    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    client_repository = ClientsRepository()
    client_id = await client_repository.get_client_id_by_uuid(str(client.uuid))

    # Get the lead whom is the person who sent the email
    lead_repository = LeadsRepository()
    lead = await lead_repository.get_lead_by_email(from_email)

    # If lead does not exist, create the lead
    if lead is None:
        lead = await lead_repository.create_lead_by_email(from_email, client_id)

    # Get Company Information
    company_information_repository = CompanyInformationRepository()

    company_information = (
        await company_information_repository.get_company_information_by_client_id(
            client_id=client_id
        )
    )

    if company_information is None:
        raise HTTPException(status_code=404, detail="Company information not found")
    
    conversation_repository = ConversationsRepository()

    # Find conversation by email_message_id
    conversation = await Conversation.filter(
        email_message_id=email_thread_ids["message_id"]
    ).get_or_none()

    messages = []

    # If conversation does not exist, create the conversation
    if conversation is None:
        conversation = await Conversation.create(
            email_message_id=email_thread_ids["message_id"],
            lead=lead,
            message_type=MessageType.EMAIL,
        )
    else:
        messages = await conversation_repository.get_messages_by_conversation(conversation.id)

    company_data = {
        "agent_name": client.ai_bot_name,
        "agent_title": "Community",
        "company_name": company_information.company_name,
        "about_us": company_information.about_us,
        "socials": json.dumps(company_information.socials),
    }

    parsed_email_for_user_message = await process_email_for_user_message(text)
    
    ## 2. Save the parsed email as a message in the conversation
    await conversation_repository.create_user_message(
            conversation_id=str(conversation.id),
            content=parsed_email_for_user_message,
            medium_response_type="email",
        )

    return client, lead, company_information, conversation, messages, conversation_repository, company_data, parsed_email_for_user_message




