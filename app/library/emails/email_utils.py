from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Header
import logging
from typing import Optional
from fastapi import HTTPException
from email.utils import parseaddr
import dotenv
import os

dotenv.load_dotenv()

logger = logging.getLogger(__name__)

# Load environment variables at module level
EMAIL_FROM = os.getenv("EMAIL_FROM")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

# Function to send email response
async def send_email_response(
    to_email: str, subject: str, body: str, in_reply_to: str, references: str, cc_emails: Optional[str] = None
):
    try:

        print("from_email: ", EMAIL_FROM)
        print("to_email: ", to_email)
        print("subject: ", subject)
        print("body: ", body)
        print("in_reply_to: ", in_reply_to)
        print("references: ", references)

        message = Mail(
            from_email=EMAIL_FROM,
            to_emails=to_email,
            subject=subject,
            html_content=body,  # Optional HTML content
        )
        
        # Add CC if provided
        if cc_emails:
            # Handle multiple CC emails (comma-separated string)
            if isinstance(cc_emails, str):
                cc_list = [email.strip() for email in cc_emails.split(',')]
            else:
                cc_list = cc_emails
            # Remove duplicates between to and cc
            cc_list = [email for email in cc_list if email != to_email]
            if cc_list:  # Only add CC if there are emails left
                message.cc = cc_list
        print("message: ", message)
        # -----------------------------------------------------------------
        #  Add the threading headers so clients know it's a reply.
        # -----------------------------------------------------------------
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

    print("headers: ", headers)

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


    print("cc: ", cc)
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
