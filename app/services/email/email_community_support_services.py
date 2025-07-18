from app.library.emails.email_utils import extract_email_thread_ids_and_set_references_and_in_reply_to_to_message_id, handle_allowed_recipients_and_cc_emails
from app.library.llm_utils import generate_ai_response
from app.prompts.emails.emails_prompt_templates import (
    provide_information_in_email_format_prompt,
    should_agent_respond_to_email_prompt,
)
from app.models.model import Client, Conversation, Lead, CompanyInformation
from app.repository.company_information_repository import CompanyInformationRepository
from app.repository.clients_repository import ClientsRepository
from app.repository.leads_repository import LeadsRepository
from app.services.email.email_services import get_client_lead_company_information_with_threading
from app.library.luma_utils import fetch_luma_events
from app.library.emails.email_utils import send_email_response
from app import constants

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

    print("from_email: ", from_email)
    print("to: ", to)
    print("subject: ", subject)
    print("cc: ", email_thread_ids["cc"])
    print("references: ", email_thread_ids["references"])
    print("in_reply_to: ", email_thread_ids["in_reply_to"])
    # print("text: ", text)

    # Extract email details
    sender = from_email
    # print("sender: ", sender)

    allowed_recipient = handle_allowed_recipients_and_cc_emails(to, headers_field)

    client, lead, company_information, conversation, messages, conversation_repository, company_data, parsed_email_for_user_message, email_thread_ids_for_save, from_email_for_save, allowed_recipient_for_save = await get_client_lead_company_information_with_threading(allowed_recipient, email_thread_ids, from_email, text, subject)

    # Should Maria Respond
    async def should_agent_respond_to_email(messages: list[dict[str, str]]) -> bool:
        should_agent_response = True

        # If the user is from Maria's email, then we should not respond
        if "maria@deepstation.ai" in sender.lower():
            print("Agent should not respond to email because sender is from Maria's email")
            should_agent_response = False
        elif email_thread_ids["cc"] is None:
            print("Agent should respond to email because cc is None")
            should_agent_response = True
        else:
            # If the user is not from Maria's email, then check the messages to see if they are talking to Maria or if the conversation is about someone else
            prompt = should_agent_respond_to_email_prompt(company_data, messages, sender, to, email_thread_ids["cc"], subject)
            
            try:
                should_agent_response_json = await generate_ai_response(prompt, messages)
                # Validate the response format
                if not isinstance(should_agent_response_json, dict) or "response" not in should_agent_response_json:
                    print(f"Invalid should_agent_response format: {should_agent_response_json}")
                    should_agent_response = True
                    print("Defaulting to should_agent_response = True due to invalid format")
                else:
                    should_agent_response = should_agent_response_json["response"]
                    print("Agent should respond to email because prompt response is: ", should_agent_response)
            except Exception as e:
                print(f"Error getting should_agent_response: {e}")
                # Default to responding if we can't determine
                should_agent_response = True
                print("Defaulting to should_agent_response = True due to error")

        print("should_agent_response: ", should_agent_response)

        return should_agent_response

    should_agent_respond = await should_agent_respond_to_email(messages)

    if not should_agent_respond:
        print("Agent should not respond to email")
        return {"status": "success", "message": "No response sent"}
    


    agent_signature = f"""
        <p>
        Warm regards,<br>
        <span style="font-weight: bold;">{company_data["agent_name"]}</span><br>
        {company_data["agent_title"]}, {company_data["company_name"]}
        </p>
        <p>
        <a href="https://www.linkedin.com/in/grant-kurz/" style="font-weight: bold; color: #1a0dab; text-decoration: none;">LinkedIn Profile</a>
        &nbsp;|&nbsp;
        <a href="https://deepstation.ai" style="font-weight: bold; color: #1a0dab; text-decoration: none;">DeepStation.AI</a>
        </p>
    """

    if constants.LUMA_API_KEY:    
        # next events
        next_events = await fetch_luma_events()
    else:
        next_events = None

    ## 3. Create a prompt for the AI to respond to the email
    prompt = provide_information_in_email_format_prompt(
        company_data, subject, parsed_email_for_user_message, sender, to, email_thread_ids["cc"], agent_signature, next_events
    )

    try:
        ai_response_json = await generate_ai_response(prompt, messages)
        # Validate the response format
        if not isinstance(ai_response_json, dict) or "response" not in ai_response_json:
            print(f"Invalid AI response format: {ai_response_json}")
            return {"status": "error", "message": "Invalid AI response format"}
    except Exception as e:
        print(f"Error generating AI response: {e}")
        return {"status": "error", "message": f"Failed to generate AI response: {e}"}

    # print("ai_response_json: ", ai_response_json)

    # print("about to send email response")
    ## 4. Send the response back first to get the message_id
    # Proper email etiquette: reply to sender, CC the original recipients
    # Extract non-sender recipients from original 'to' field
    original_recipients = [addr.strip() for addr in to.split(',') if addr.strip() != sender]
    
    # Combine original recipients with existing CC (if any)
    combined_cc = []
    if original_recipients:
        combined_cc.extend(original_recipients)
    if email_thread_ids["cc"]:
        existing_cc = [addr.strip() for addr in email_thread_ids["cc"].split(',')]
        combined_cc.extend(existing_cc)
    
    # Remove duplicates and sender from CC list
    combined_cc = list(set(combined_cc))
    combined_cc = [addr for addr in combined_cc if addr != sender]
    
    final_cc = ','.join(combined_cc) if combined_cc else None
    
    print(f"🔍 DEBUG: final_cc type: {type(final_cc)}, value: {final_cc}")
    print(f"🔍 DEBUG: sender: {sender}")
    print(f"🔍 DEBUG: subject: {subject}")
    print(f"🔍 DEBUG: in_reply_to: {email_thread_ids['in_reply_to']}")
    print(f"🔍 DEBUG: references: {email_thread_ids['references']}")
    
    try:
        assistant_message_id = await send_email_response(
            sender,  # Reply to the original sender
            subject,
            ai_response_json["response"],
            email_thread_ids["in_reply_to"],
            email_thread_ids["references"],
            final_cc,  # CC everyone else
        )
    except Exception as e:
        print(f"Error sending email response: {e}")
        return {"status": "error", "message": f"Failed to send email response: {e}"}
    
    # Build new references header for the assistant message
    new_references = []
    if email_thread_ids["references"]:
        # If references is a string, split it; if it's a list, use it
        if isinstance(email_thread_ids["references"], str):
            new_references = [ref.strip('<>') for ref in email_thread_ids["references"].split()]
        else:
            new_references = email_thread_ids["references"]
    
    # Add the original message_id to references
    if email_thread_ids["message_id"]:
        new_references.append(email_thread_ids["message_id"].strip('<>'))
    
    ## 5. Save the AI response as a message in the conversation with threading fields
    # Strip brackets from message_id for consistent database storage
    clean_assistant_message_id = assistant_message_id.strip('<>')
    clean_in_reply_to = email_thread_ids["message_id"].strip('<>') if email_thread_ids["message_id"] else None
    
    print(f"💾 Saving assistant message with message_id: '{clean_assistant_message_id}'")
    print(f"💾 Assistant in_reply_to: '{clean_in_reply_to}'")
    print(f"💾 Assistant references: {new_references}")
    
    await conversation_repository.create_assistant_message(
        conversation_id=str(conversation.id),
        content=ai_response_json["response"],
        medium_response_type="email",
        message_id=clean_assistant_message_id,
        in_reply_to=clean_in_reply_to,  # Reply to the user's message
        references=new_references,
        from_addr=allowed_recipient,  # The AI agent's email
        to_addr=sender,  # Reply to the original sender
        subject=subject,
        email_date=None,  # Could add current timestamp if needed
    )
    print("💾 Assistant message saved to database")
    print("email response sent")
    return {"status": "success", "message": "Response sent"}
