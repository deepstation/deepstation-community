import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Header
import logging

logger = logging.getLogger(__name__)


# Function to send email response
async def send_email_response(
    to_email: str, subject: str, body: str, in_reply_to: str, references: str
):
    from_email = os.getenv("EMAIL_SENDER")
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")

    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=body,  # Optional HTML content
    )

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
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        logger.info(f"Email sent: {response.status_code}")
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise


def extract_email_thread_ids(headers: str) -> dict:
    """
    Takes the raw headers string from an inbound email (like `headers_field`)
    and returns a dictionary with keys:
      - message_id
      - in_reply_to
      - references

    The function looks for lines that start with:
      - "Message-ID:"
      - "In-Reply-To:"
      - "References:"
    and captures whatever is after the colon.
    """
    message_id = None
    in_reply_to = None
    references = None

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

    return {
        "message_id": message_id,
        "in_reply_to": in_reply_to,
        "references": references,
    }
