from app.library.emails.email_utils import extract_email_thread_ids_and_set_references_and_in_reply_to_to_message_id, handle_allowed_recipients_and_cc_emails
from app.library.llm_utils import generate_ai_response
from app.prompts.emails.emails_prompt_templates import (
    provide_information_in_email_format_prompt,
)
from app.models.model import Client, Conversation, Lead, CompanyInformation
from app.repository.company_information_repository import CompanyInformationRepository
from app.repository.clients_repository import ClientsRepository
from app.repository.leads_repository import LeadsRepository
from app.services.email.email_services import get_client_lead_company_information
from app.library.luma_utils import fetch_luma_events
from app.library.emails.email_utils import send_email_response

async def community_support_email_service(to: str, from_email: str, subject: str, text: str, headers_field: str):
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
    email_thread_ids = extract_email_thread_ids_and_set_references_and_in_reply_to_to_message_id(headers_field)

    ### DEBUGGING ###
    # print("raw_headers: ", raw_headers)
    # print("raw_response: ", raw_body)

    # print("from_email: ", from_email)
    # print("to: ", to)
    # print("subject: ", subject)
    # print("text: ", text)

    # Extract email details
    sender = from_email

    allowed_recipient = handle_allowed_recipients_and_cc_emails(to, headers_field)


    client, lead, company_information, conversation, messages, conversation_repository, company_data, parsed_email_for_user_message = await get_client_lead_company_information(allowed_recipient, email_thread_ids, from_email, text)


    agent_signature = """
    Warm regards,
    **Maria Agentica**
    Community, DeepStation

    [**LinkedIn Profile**](https://www.linkedin.com/in/grant-kurz/)
    [**DeepStation.AI**](https://deepstation.ai)
    """

    # next events
    next_events = await fetch_luma_events()

    ## 3. Create a prompt for the AI to respond to the email
    prompt = provide_information_in_email_format_prompt(
        company_data, subject, text, agent_signature, next_events
    )

    ai_response_json = await generate_ai_response(prompt, messages)

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
