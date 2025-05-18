from calendar import day_name
import json
from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.library.llm_utils import call_llm
from app.library.sms_utils import send_sms_to
from app.models.model import Client, Lead, Message, Conversation, Campaign
from app.prompts.sms.blasts_prompts import event_invitation_prompt_template
from app.prompts.sms.community_support_prompts import event_community_support_prompt_template
from typing import List, Dict
from app.fixtures.events.luma import luma_events
from app.fixtures.community.community_fixtures import gptechday_community
from app.fixtures.bot_details import gptechday_volunteer_bot
from pprint import pprint

sms_router = APIRouter()

class SendSmsRequest(BaseModel):
    lead_uuid: str
    client_uuid: str
    time_of_call: str
    
class SmsBlastRequest(BaseModel):
    list: List[Dict[str, str]]
    campaign_uuid: str
    client_uuid: str

# Webhooks
@sms_router.post("/api/sms/webhook")
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

@sms_router.post("/api/sms/blast")
async def sms_blast(request: SmsBlastRequest):
    results = []
    try:
        # Get client
        client = await Client.get(uuid=request.client_uuid)
        for lead_info in request.list:
            phone_number = lead_info["phone_number"]
            lead_name = lead_info["name"]
            campaign = await Campaign.get(uuid=request.campaign_uuid)
            # Find or create lead
            lead = await Lead.get_or_none(ai_phone_number=phone_number, client=client)
            if not lead:
                lead = await Lead.create(
                    name=lead_name,
                    ai_phone_number=phone_number,
                    client=client
                )
            # Get or create conversation for this lead
            conversation = await Conversation.get_or_none(lead=lead)
            if not conversation:
                conversation = await Conversation.create(lead=lead)
            # Update conversation tags to only store campaign UUIDs
            conversation_tags = conversation.tags or {}
            campaign_uuids = set(conversation_tags.get("campaign_uuids", []))
            campaign_uuid_str = str(campaign.uuid)
            campaign_uuids.add(campaign_uuid_str)
            conversation_tags["campaign_uuids"] = list(campaign_uuids)
            conversation.tags = conversation_tags
            await conversation.save()

            # Generate AI Response
            """
            1. Use campaign uuid to get the related campaign name
            2. Use campaign name to get the event context
            3. Use event context for the prompt template
            4. Use lead name for the prompt template
            """

            campaign_name = campaign.name
            event_context = luma_events[campaign_name]

            print("Event Context: ", event_context)


            prompt_template = event_invitation_prompt_template(event_context, lead_name, gptechday_community)

            assistant_message = {
                "role": "assistant",
                "content": prompt_template
            }

            llm_response = await call_llm([assistant_message])
            llm_response = json.loads(llm_response)

            # Create message
            created_message = await Message.create(
                conversation=conversation,
                content=llm_response["content"],
                role="assistant"
            )
            # Send SMS
            try:
                send_sms_to(
                    from_number=client.ai_phone_number,
                    to_number=phone_number,
                    body=llm_response["content"]
                )
                results.append({"phone_number": phone_number, "status": "sent"})
            except Exception as sms_error:
                results.append({"phone_number": phone_number, "status": "failed", "error": str(sms_error)})
        return {"results": results}
    except Exception as e:
        return {"error": str(e)}, 400

# Webhooks
@sms_router.post("/api/sms/webhook/alternative")
async def receive_sms(
    request: Request
):
    """
    This alternative webhook will preferably ise Telnyx as the SMS provider.
    """
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
