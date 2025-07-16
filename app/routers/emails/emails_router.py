from fastapi import APIRouter, HTTPException, Form
from app.library.emails.email_utils import send_email_response, extract_email_thread_ids
from app.library.llms import chat_completion_request
from app.prompts.emails.emails_prompt_templates import (
    provide_information_in_email_format_prompt,
)
from app.models.model import Client, Conversation
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
from email.utils import parseaddr
from app.library.luma_utils import fetch_luma_events
ALLOWED = ["maria@deepstation.ai", "maria@inbound-email.deepstation.ai"]

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
    """
    Args:
      to: str = Form(...)
      from_email: str = Form(..., alias="from")
      subject: str = Form(...)
      text: str = Form(None)

    Purpose:
      - Handle incoming emails
      - Generate an AI response
      - Send the response back to the sender
    """
    try:
        # print("headers_field: ", headers_field)

        print("to: ", to)
        print("from_email: ", from_email)
        print("subject: ", subject)
        print("headers_field: ", headers_field)


        email_thread_ids = extract_email_thread_ids(headers_field)

        def is_email_threads_ids_references_and_in_reply_to_none(email_thread_ids):
            if (
                email_thread_ids["references"] is None
                and email_thread_ids["in_reply_to"] is None
            ):
                email_thread_ids["references"] = email_thread_ids["message_id"]
                email_thread_ids["in_reply_to"] = email_thread_ids["message_id"]

                # print("message_id")

            return email_thread_ids

        email_thread_ids = is_email_threads_ids_references_and_in_reply_to_none(
            email_thread_ids
        )

        print("email_thread_ids: ", email_thread_ids)

        # print("raw_headers: ", raw_headers)
        # print("raw_response: ", raw_body)

        # print("from_email: ", from_email)
        # print("to: ", to)
        # print("subject: ", subject)
        # print("text: ", text)

        # Parse all recipients from the to field (handles CC scenarios)
        to_recipients = [parseaddr(addr.strip())[1].lower() for addr in to.split(',')]
        allowed_recipient = None
        
        for recipient in to_recipients:
            if recipient in ALLOWED:
                allowed_recipient = recipient
                break
        
        # If no allowed recipient found in form data, check headers
        if allowed_recipient is None and headers_field:
            for line in headers_field.splitlines():
                if line.lower().startswith("to:"):
                    header_to = line.split(":", 1)[1].strip()
                    header_recipients = [parseaddr(addr.strip())[1].lower() for addr in header_to.split(',')]
                    for recipient in header_recipients:
                        if recipient in ALLOWED:
                            allowed_recipient = recipient
                            break
                    if allowed_recipient:
                        break

        if allowed_recipient is None:
            print("to_recipients: ", to_recipients)
            raise HTTPException(
                status_code=403,
                detail="This email is not addressed to the allowed recipient.",
            )

        try:
            # Extract email details
            sender = from_email
            subject = subject

            # print("text: ", text)
            logger.info(f"text: {text}")
            print("##############End Text############")

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

            # print("lead: ", lead)

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
                "agent_name": "Maria",
                "agent_title": "DeepStation Agent",
                "company_name": company_information.company_name,
                "about_us": company_information.about_us,
                "socials": json.dumps(company_information.socials),
            }

            # Find conversation by email_message_id
            conversation = await Conversation.filter(
                email_message_id=email_thread_ids["message_id"]
            ).get_or_none()

            # If conversation does not exist, create the conversation
            if conversation is None:
                conversation = await Conversation.create(
                    email_message_id=email_thread_ids["message_id"],
                    lead=lead,
                    message_type=MessageType.EMAIL,
                )

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

            print("parsed_emailfor_first_message: ", parsed_email_for_user_message)

            ## 2. Save the parsed email as a message in the conversation
            conversation_repository = ConversationsRepository()

            await conversation_repository.create_user_message(
                conversation_id=str(conversation.id),
                content=parsed_email_for_user_message,
                medium_response_type="email",
            )

            print("conversation: ", conversation)

            agent_signature = """
            Warm regards,
            **Maria Agentica**
            Community, DeepStation

            [**LinkedIn Profile**](https://www.linkedin.com/in/grant-kurz/)
            [**DeepStation.AI**](https://deepstation.ai)
            """

            # next events
            next_events = await fetch_luma_events()
            # print("next_events: ", next_events)

            ## 3. Create a prompt for the AI to respond to the email
            prompt = provide_information_in_email_format_prompt(
                company_data, subject, text, agent_signature, next_events
            )

            messages = [{"role": "user", "content": prompt}]

            # Generate an AI response
            ai_response = await chat_completion_request(messages, model="gpt-4o")

            if ai_response is None:
                raise HTTPException(status_code=500, detail="Failed to generate AI response")

            ai_response_json = json.loads(ai_response)

            # print("ai_response_json: ", ai_response_json)

            ## 4. Save the AI response as a message in the conversation
            await conversation_repository.create_assistant_message(
                conversation_id=str(conversation.id),
                content=ai_response_json["response"],
                medium_response_type="email",
            )

            # print("about to send email response")
            ## 5. Send the response back
            await send_email_response(
                sender,
                subject,
                ai_response_json["response"],
                email_thread_ids["in_reply_to"],
                email_thread_ids["references"],
                email_thread_ids["cc"],
            )
            print("email response sent")
            return {"status": "success", "message": "Response sent"}

        except Exception as e:
            print("error: ", e)
            logger.error(f"Error in handle_email: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    except Exception as error:
        print("error: ", error)
        logger.error(f"Error in handle_email: {error}")
        raise HTTPException(status_code=500, detail=str(error))
