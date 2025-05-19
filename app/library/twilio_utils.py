def get_to_from_body_from_twilio_object_webhook(data):
    member_number = data["From"]
    community_number = data["To"]
    body = data["Body"]
    return member_number, community_number, body