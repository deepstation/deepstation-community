# Potentially deprecated for the sms_utils twilio post function (move that one into here)

"""
import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")

client = Client(twilio_account_sid, twilio_auth_token)

def send_sms_message(from_number: str, to_number: str, message: str):
    client.messages.create(
        # From signifies virtual number from Twilio?
        from_=from_number,
        to=to_number,
        body=message
    )
"""
def get_to_from_body_from_twilio_object_webhook(data):
    member_number = data["From"]
    community_number = data["To"]
    body = data["Body"]
    return member_number, community_number, body