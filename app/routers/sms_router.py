from fastapi import APIRouter, Request, Depends
from app.pydantic_models.pydantic_index import SmsBlastRequest
from app.services.sms.community_support_services import community_support_webhook_service, sms_blast_service_batch, sms_blast_service_mass_batch, sms_blast_service_batch_whatsapp_group
from app.dependencies.auth import get_api_key

sms_router = APIRouter()

@sms_router.post("/api/sms/webhook", dependencies=[
    Depends(get_api_key)
])
async def receive_sms(
    request: Request
):
    try:
        return await community_support_webhook_service(request)
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return {"error": "Invalid JSON payload"}, 400

@sms_router.post("/api/sms/blast")
async def sms_blast(request: SmsBlastRequest):
    try:
        results = await sms_blast_service_batch(request)
        return {"results": results}
    except Exception as e:
        return {"error": str(e)}, 400
    
@sms_router.post("/api/sms/blast/whatsapp-group")
async def sms_blast_whatsapp_group(request: SmsBlastRequest):
    try:
        print("Request: ", request)
        results = await sms_blast_service_batch_whatsapp_group(request)
        return {"results": results}
    except Exception as e:
        return {"error": str(e)}, 400


"""
Keeping as backup until async gather is finalized.
# Webhooks
@sms_router.post("/api/sms/webhook/alternative")
async def receive_sms(
    request: Request
):

    try:
        data = await request.form()
        lead_number = data["From"]
        client_number = data["To"]
        body = data["Body"]

        # Get client and lead
        client = await Client.get(ai_phone_number=client_number)
        lead = await Lead.get(ai_phone_number=lead_number)

        # Find the conversation for this lead
        conversation = await Conversation.get_or_none(lead=lead)
        if not conversation:
            conversation = await Conversation.create(lead=lead)

        # Extract campaign UUIDs from conversation tags
        campaign_uuids = conversation.tags.get("campaign_uuids", []) if conversation.tags else []

        # Aggregate full event context objects for all campaigns
        event_contexts = []
        for campaign_uuid in campaign_uuids:
            campaign = await Campaign.get_or_none(uuid=campaign_uuid)
            if campaign:
                event_name = campaign.name
                event_context = luma_events.get(event_name)
                if event_context:
                    event_contexts.append(event_context)

        # Pass the list of event context objects to the prompt template
        prompt_template = event_community_support_prompt_template(
            event_context=event_contexts,
            lead_name=lead.name,
            community_context=gptechday_community,
            user_message=body
        )

        # Call LLM
        system_message = {
            "role": "system",
            "content": prompt_template
        }

        # Save message
        await Message.create(
            conversation=conversation,
            content=body,
            role="user"
        )

        # Get messages
        messages = await Message.filter(conversation=conversation)

        print("Messages: ", messages)

        message_history = []
        message_history.append(system_message)

        # Only include the most recent 15 messages
        recent_messages = list(messages)[-15:]
        for message in recent_messages:
            message_history.append({"role": message.role, "content": message.content})

        for message in recent_messages:
            print("Role: ", message.role)
            print("Content: ", message.content)

        pprint(message_history)
        # print("Message History: ", message_history)
        llm_response = await call_llm(message_history)
        llm_response = json.loads(llm_response)

        print("LLM Response: ", llm_response)

        # Save the assistant's response
        await Message.create(
            conversation=conversation,
            content=llm_response["content"],
            role="assistant"
        )

        # Optionally, send SMS back to the user
        send_sms_to(
            from_number=client.ai_phone_number,
            to_number=lead.ai_phone_number,
            body=llm_response["content"]
        )

        return {"message": "SMS received"}
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return {"error": "Invalid JSON payload"}, 400
"""