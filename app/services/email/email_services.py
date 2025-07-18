from app.models.model import Client, Lead, CompanyInformation, Conversation, MessageType, Message
from app.repository.clients_repository import ClientsRepository
from app.repository.leads_repository import LeadsRepository
from app.repository.company_information_repository import CompanyInformationRepository
from app.repository.conversations_repository import ConversationsRepository
from fastapi import HTTPException
import json
from app.prompts.emails.emails_prompt_templates import parse_email_response_for_only_sent_message_prompt
from app.library.llms import chat_completion_request
from pydantic import BaseModel

async def process_email_for_user_message(text: str) -> dict:
    
    # If conversation, save the sent message.
    ## 1. Parse the email and get the most recent message
    parsed_emailfor_first_message_prompt = (
        parse_email_response_for_only_sent_message_prompt(text)
    )

    parsed_email_for_user_message = await chat_completion_request(
        [{"role": "user", "content": parsed_emailfor_first_message_prompt}],
        model="gpt-4.1",
    )

    if parsed_email_for_user_message is None:
        raise HTTPException(status_code=500, detail="Failed to parse email content")

    parsed_email_for_user_message = json.loads(parsed_email_for_user_message)

    return parsed_email_for_user_message

async def get_client_lead_company_information_with_threading(allowed_recipient: str, email_thread_ids: dict, from_email: str, text: str, subject: str) -> tuple[Client, Lead, CompanyInformation, Conversation, list[dict[str, str]], ConversationsRepository, dict, str, dict, str, str]:
    """
    New implementation using robust email threading logic.
    """
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
    
    company_data = {
        "agent_name": client.ai_bot_name,
        "agent_title": "Community",
        "company_name": company_information.company_name,
        "about_us": company_information.about_us,
        "socials": json.dumps(company_information.socials),
    }

    conversation_repository = ConversationsRepository()

    # Parse email content first to get the user message
    parsed_email_for_user_message = await process_email_for_user_message(text)
    
    # Find or create conversation WITHOUT saving the message yet
    from app.library.emails.email_utils import find_or_create_conversation
    
    conversation = await find_or_create_conversation(
        message_id=email_thread_ids["message_id"],
        in_reply_to=email_thread_ids["in_reply_to"],
        references=email_thread_ids["references"],
        lead_id=lead.id,
        campaign_id=None,  # You can pass campaign_id if needed
    )
    
    print("Conversation resolved: ", conversation)
    print("Current email message_id: ", email_thread_ids["message_id"])
    print("In reply to: ", email_thread_ids["in_reply_to"])
    print("References: ", email_thread_ids["references"])
    
    # If the user is not from our bots email, then we should save the message 
    if "maria@deepstation.ai" not in from_email.lower():
        print("Agent should not respond to email because sender is from Maria's email")
        should_agent_response = False

        # Agent will respond - now save the user message
        from app.library.emails.email_utils import save_user_message
        
        await save_user_message(
            conversation_id=conversation.id,
            message_id=email_thread_ids["message_id"],
            in_reply_to=email_thread_ids["in_reply_to"],
            references=email_thread_ids["references"],
            content=parsed_email_for_user_message["response"],
            from_addr=from_email,
            to_addr=allowed_recipient,
            subject=subject,
            email_date=None,
        )
        print("User message saved")

    # Get conversation messages for context (existing messages only)
    messages = await conversation_repository.get_messages_by_conversation(conversation.id)
    # Limit to 15 messages for context
    messages = messages[-15:]
    
    # Convert to list of dicts with role and content
    messages = [{"role": message.role, "content": message.content} for message in messages]
    print("Messages retrieved: ", messages)

    return client, lead, company_information, conversation, messages, conversation_repository, company_data, parsed_email_for_user_message["response"], email_thread_ids, from_email, allowed_recipient


async def get_client_lead_company_information(allowed_recipient: str, email_thread_ids: dict, from_email: str, text: str) -> tuple[Client, Lead, CompanyInformation, Conversation, list[dict[str, str]], ConversationsRepository, dict, str]:
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
    
    company_data = {
        "agent_name": client.ai_bot_name,
        "agent_title": "Community",
        "company_name": company_information.company_name,
        "about_us": company_information.about_us,
        "socials": json.dumps(company_information.socials),
    }

    conversation_repository = ConversationsRepository()

    # Find conversation by email_message_id
    # For reply emails, use in_reply_to to find existing conversation
    # For new threads, use message_id to check if conversation already exists
    # search_message_id = email_thread_ids["in_reply_to"] if email_thread_ids["in_reply_to"] else email_thread_ids["message_id"]
    
    # TODO: This is a temporary fix as this is not scalable. We need a better way to handle threads. Open source options?
    search_message_id = email_thread_ids["message_id"]
    print(f"Searching for conversation using: {repr(search_message_id)}")
    print(f"Is reply email: {email_thread_ids['in_reply_to'] is not None}")
    
    conversation = await Conversation.filter(
        email_message_id=search_message_id,
    ).get_or_none()

    messages = []

    print("Conversation found: ", conversation)
    print("Current email message_id: ", email_thread_ids["message_id"])
    print("In reply to: ", email_thread_ids["in_reply_to"])
    
    async def process_email_and_create_user_message(conversation: Conversation, text: str):
        parsed_email_for_user_message = await process_email_for_user_message(text)

        await conversation_repository.create_user_message(
            conversation_id=str(conversation.id),
            content=parsed_email_for_user_message["response"],
            medium_response_type="email",
        )

        return parsed_email_for_user_message
    
    if conversation:
        parsed_email_for_user_message = await process_email_and_create_user_message(conversation, text)
        messages = await conversation_repository.get_messages_by_conversation(conversation.id)
        # limit to 10 messages
        messages = messages[-15:]

        # convert these to a list of dicts role and content
        messages = [{"role": message.role, "content": message.content} for message in messages]
        print("Conversation Exists, retrieving messages")
        print("Messages retrieved: ", messages)
    # If conversation does not exist, create the conversation
    else:
        print("Conversation does not exist, creating conversation")
        conversation = await Conversation.create(
            email_message_id=email_thread_ids["message_id"],
            lead=lead,
            message_type=MessageType.EMAIL,
        )

        print("Conversation created: ", conversation)

        parsed_email_for_user_message = await process_email_and_create_user_message(conversation, text)

        messages = await conversation_repository.get_messages_by_conversation(conversation.id)
        # limit to 10 messages
        messages = messages[-15:]
        # convert these to a list of dicts role and content
        messages = [{"role": message.role, "content": message.content} for message in messages]

    print("messages: ", messages)

    return client, lead, company_information, conversation, messages, conversation_repository, company_data, parsed_email_for_user_message["response"]




