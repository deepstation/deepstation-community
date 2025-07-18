from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Header
import logging
from typing import Optional, List
from fastapi import HTTPException
from email.utils import parseaddr
import dotenv
import os
from tortoise.transactions import in_transaction

dotenv.load_dotenv()

logger = logging.getLogger(__name__)

# Load environment variables at module level
EMAIL_FROM = os.getenv("EMAIL_FROM")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

# Function to send email response
async def send_email_response(
    to_email: str, subject: str, body: str, in_reply_to: str, references: str, cc_emails: Optional[str] = None
) -> str:
    import uuid
    import time
    import socket
    
    print(f"🔍 DEBUG send_email_response params:")
    print(f"  to_email: {to_email} (type: {type(to_email)})")
    print(f"  subject: {subject} (type: {type(subject)})")
    print(f"  body: {body} (type: {type(body)})")
    print(f"  in_reply_to: {in_reply_to} (type: {type(in_reply_to)})")
    print(f"  references: {references} (type: {type(references)})")
    print(f"  cc_emails: {cc_emails} (type: {type(cc_emails)})")
    
    try:
        # Generate a unique Message-ID for the outgoing email
        timestamp = int(time.time())
        hostname = socket.gethostname()
        unique_id = str(uuid.uuid4())[:8]
        message_id = f"<{unique_id}-{timestamp}@{hostname}>"
        
        # DEBUGGING
        # print("from_email: ", EMAIL_FROM)
        # print("to_email: ", to_email)
        # print("subject: ", subject)
        # print("body: ", body)
        # print("in_reply_to: ", in_reply_to)
        # print("references: ", references)

        print(f"🔍 DEBUG: Creating Mail object with:")
        print(f"  from_email: {EMAIL_FROM}")
        print(f"  to_emails: {to_email}")
        print(f"  subject: {subject}")
        print(f"  html_content: {body}")
        
        message = Mail(
            from_email=EMAIL_FROM,
            to_emails=to_email,
            subject=subject,
            html_content=body,  # Optional HTML content
        )
        
        print(f"🔍 DEBUG: Mail object created successfully")
        
        # Add CC if provided
        if cc_emails:
            print(f"🔍 DEBUG: Processing CC emails: {cc_emails} (type: {type(cc_emails)})")
            # Handle multiple CC emails (comma-separated string)
            if isinstance(cc_emails, str):
                # Use email.utils.getaddresses to properly parse email addresses
                from email.utils import getaddresses
                # Parse the CC string into proper email addresses
                parsed_addresses = getaddresses([cc_emails])
                cc_list = [addr[1] for addr in parsed_addresses if addr[1]]  # Extract just the email addresses
                print(f"🔍 DEBUG: CC list from parsed addresses: {cc_list}")
            else:
                cc_list = cc_emails
                print(f"🔍 DEBUG: CC list (not string): {cc_list}")
            # Remove duplicates between to and cc
            cc_list = [email for email in cc_list if email != to_email]
            print(f"🔍 DEBUG: Final CC list after duplicate removal: {cc_list}")
            if cc_list:  # Only add CC if there are emails left
                print(f"🔍 DEBUG: Setting message.cc = {cc_list}")
                message.cc = cc_list
                print(f"🔍 DEBUG: message.cc set successfully")
        print("message: ", message)
        # -----------------------------------------------------------------
        #  Add the threading headers so clients know it's a reply.
        # -----------------------------------------------------------------
        # Add our generated Message-ID
        message.add_header(Header(key="Message-ID", value=message_id))
        
        # If there's an "In-Reply-To" from the original email, attach it:
        if in_reply_to:
            message.add_header(Header(key="In-Reply-To", value=in_reply_to))

        # If there's a "References" line, attach that too:
        if references:
            message.add_header(Header(key="References", value=references))

        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)
            logger.info(f"Email sent: {response.status_code}")
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            raise
        
        # Return the message_id so it can be used for threading
        return message_id
    except Exception as e:
        print("Error in send_email_response: ", e)
        logger.error(f"Error in send_email_response: {e}")
        raise


def extract_email_thread_ids(headers: str) -> dict:
    """
    Takes the raw headers string from an inbound email (like `headers_field`)
    and returns a dictionary with keys:
      - message_id
      - in_reply_to
      - references
      - cc

    The function looks for lines that start with:
      - "Message-ID:"
      - "In-Reply-To:"
      - "References:"
      - "CC:"
    and captures whatever is after the colon.
    """
    message_id = None
    in_reply_to = None
    references = None
    original_to  = None  # New
    cc = None

    # print("headers: ", headers)

    # Split the big headers string by newlines and iterate
    for line in headers.split("\n"):
        line_stripped = line.strip()
        if line_stripped.lower().startswith("message-id:"):
            # everything after 'Message-gID:' is the actual value
            message_id = line_stripped.split(":", 1)[1].strip()
        elif line_stripped.lower().startswith("in-reply-to:"):
            in_reply_to = line_stripped.split(":", 1)[1].strip()
        elif line_stripped.lower().startswith("references:"):
            references = line_stripped.split(":", 1)[1].strip()
        elif line_stripped.lower().startswith("x-gm-original-to:"):
            original_to = line_stripped.split(":", 1)[1].strip()
        elif line_stripped.lower().startswith("cc:"):
            cc = line_stripped.split(":", 1)[1].strip()

    # print("in reply to: ", in_reply_to)
    # print("cc: ", cc)
    return {
        "message_id": message_id,
        "in_reply_to": in_reply_to,
        "references": references,
        "original_to": original_to,
        "cc": cc,
    }

ALLOWED = ["maria@deepstation.ai", "maria@inbound-email.deepstation.ai"]


def is_email_threads_ids_references_and_in_reply_to_none(email_thread_ids):
    if (
        email_thread_ids["references"] is None
        and email_thread_ids["in_reply_to"] is None
    ):
        email_thread_ids["references"] = email_thread_ids["message_id"]
        email_thread_ids["in_reply_to"] = email_thread_ids["message_id"]

    return email_thread_ids

def handle_allowed_recipients_and_cc_emails(to: str, headers_field: str) -> str:
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
    
    # If still no allowed recipient found, check CC field in headers
    if allowed_recipient is None and headers_field:
        for line in headers_field.splitlines():
            if line.lower().startswith("cc:"):
                header_cc = line.split(":", 1)[1].strip()
                cc_recipients = [parseaddr(addr.strip())[1].lower() for addr in header_cc.split(',')]
                for recipient in cc_recipients:
                    if recipient in ALLOWED:
                        allowed_recipient = recipient
                        break
                if allowed_recipient:
                    break

    if allowed_recipient is None:
        raise HTTPException(
            status_code=403,
            detail="This email is not addressed to the allowed recipient.",
        )
    
    return allowed_recipient

def extract_email_thread_ids_and_set_references_and_in_reply_to_to_message_id(headers_field: str):
    email_thread_ids = extract_email_thread_ids(headers_field)
    email_thread_ids = is_email_threads_ids_references_and_in_reply_to_none(email_thread_ids)
    return email_thread_ids


async def find_or_create_conversation(
    message_id: str,
    in_reply_to: Optional[str],
    references: Optional[str],
    lead_id: int,
    campaign_id: Optional[int] = None,
):
    """
    Find or create conversation without saving the message yet.
    This allows us to check if agent should respond before saving anything.
    """
    from app.models.model import Conversation, Message, MessageType
    
    # Parse references into a list
    refs: List[str] = []
    if references:
        refs = [r.strip('<>') for r in references.split() if r.strip()]
    
    async with in_transaction():
        # 1️⃣ Deduplication - check if we already stored this message
        existing_message = await Message.filter(message_id=message_id).select_related('conversation').first()
        if existing_message:
            logger.info(f"Message {message_id} already exists, returning existing conversation")
            return existing_message.conversation
        
        conv = None
        
        # 2️⃣ Try direct parent via In-Reply-To
        if in_reply_to:
            search_id = in_reply_to.strip('<>')
            print(f"🔍 Searching for In-Reply-To: '{search_id}'")
            parent_message = await Message.filter(message_id=search_id).select_related('conversation').first()
            if parent_message:
                conv = parent_message.conversation
                logger.info(f"Found conversation via In-Reply-To: {in_reply_to}")
                print(f"✅ Found parent message ID {parent_message.id} in conversation {conv.id}")
            else:
                print(f"❌ No parent message found for In-Reply-To: '{search_id}'")
        
        # 3️⃣ Fallback through References header (right to left)
        if conv is None and refs:
            print(f"🔍 Searching through References: {refs}")
            for ref_id in reversed(refs):
                search_id = ref_id.strip('<>')
                print(f"🔍 Trying reference: '{search_id}'")
                parent_message = await Message.filter(message_id=search_id).select_related('conversation').first()
                if parent_message:
                    conv = parent_message.conversation
                    logger.info(f"Found conversation via References: {ref_id}")
                    print(f"✅ Found parent message ID {parent_message.id} in conversation {conv.id}")
                    break
                else:
                    print(f"❌ No parent message found for reference: '{search_id}'")
        
        # 4️⃣ Start new conversation if nothing matched
        if conv is None:
            conv = await Conversation.create(
                lead_id=lead_id,
                campaign_id=campaign_id,
                message_type=MessageType.EMAIL,
            )
            logger.info(f"Created new conversation for message {message_id}")
        
        # Note: We don't save the message here - that happens later if agent responds
    
    return conv

async def save_user_message(
    conversation_id: int,
    message_id: str,
    in_reply_to: Optional[str],
    references: Optional[str],
    content: str,
    from_addr: Optional[str] = None,
    to_addr: Optional[str] = None,
    subject: Optional[str] = None,
    email_date: Optional[str] = None,
):
    """
    Save a user message to the conversation with deduplication.
    """
    from app.models.model import Message, MessageType
    
    # Parse references into a list
    refs: List[str] = []
    if references:
        refs = [r.strip('<>') for r in references.split() if r.strip()]
    
    try:
        return await Message.create(
            conversation_id=conversation_id,
            content=content,
            role="user",
            message_type=MessageType.EMAIL,
            message_id=message_id.strip('<>'),  # Ensure consistent format
            in_reply_to=in_reply_to.strip('<>') if in_reply_to else None,
            references=refs,
            from_addr=from_addr,
            to_addr=to_addr,
            subject=subject,
            email_date=email_date,
        )
    except Exception as e:
        if "duplicate key value violates unique constraint" in str(e):
            # Message already exists, find and return it
            logger.info(f"Message {message_id} already exists, skipping save")
            existing_message = await Message.filter(message_id=message_id.strip('<>')).first()
            return existing_message
        else:
            # Re-raise other exceptions
            raise

async def touch_conversation(
    message_id: str,
    in_reply_to: Optional[str],
    references: Optional[str],
    lead_id: int,
    campaign_id: Optional[int] = None,
    from_addr: Optional[str] = None,
    to_addr: Optional[str] = None,
    subject: Optional[str] = None,
    content: Optional[str] = None,
    email_date: Optional[str] = None,
):
    """
    Robust email threading resolver that finds or creates the correct Conversation and saves the message.
    
    Args:
        message_id: RFC 5322 Message-ID
        in_reply_to: RFC 5322 In-Reply-To header
        references: RFC 5322 References header (space-separated string)
        lead_id: ID of the lead who sent the email
        campaign_id: Optional campaign ID
        from_addr: Email from address
        to_addr: Email to address
        subject: Email subject
        content: Email content
        email_date: Email date header
    
    Returns:
        Conversation object the message belongs to
    """
    # Find or create conversation
    conv = await find_or_create_conversation(
        message_id=message_id,
        in_reply_to=in_reply_to,
        references=references,
        lead_id=lead_id,
        campaign_id=campaign_id,
    )
    
    # Save the user message
    await save_user_message(
        conversation_id=conv.id,
        message_id=message_id,
        in_reply_to=in_reply_to,
        references=references,
        content=content or "",
        from_addr=from_addr,
        to_addr=to_addr,
        subject=subject,
        email_date=email_date,
    )
    
    logger.info(f"Stored message {message_id} in conversation {conv.id}")
    
    return conv
