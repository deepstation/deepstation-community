from fastapi import Request
from app.library.twilio_utils import get_to_from_body_from_twilio_object_webhook
from app.models.model import Client
from app.models.model import Lead
from app.models.model import Conversation
from app.models.model import Campaign
from app.models.model import Message
from app.prompts.sms.blasts_prompts import event_invitation_prompt_template, whatsapp_group_invitation_prompt_template
from app.prompts.sms.community_support_prompts import event_community_support_prompt_template
from app.fixtures.events.luma import luma_events
from app.fixtures.community_fixtures import gptechday_community
from pprint import pprint
import json
from app.library.llm_utils import call_llm
from app.pydantic_models.pydantic_index import SmsBlastRequest
from app.tasks.sms_tasks import send_sms_to_rate_limited_task
import httpx
from datetime import datetime, timezone
import os
import asyncio
from app.library.luma_utils import fetch_luma_events

LUMA_API_KEY = os.getenv("LUMA_API_KEY")
LUMA_LIST_EVENTS_URL = "https://public-api.lu.ma/public/v1/calendar/list-events"


async def community_support_webhook_service(request: Request):
    try:
        data = await request.form()

        member_number, community_number, body = get_to_from_body_from_twilio_object_webhook(data)

        # Ensure body is a string
        if not isinstance(body, str):
            body = str(body)

        # Fetch upcoming events from Lu.ma
        event_contexts = await fetch_luma_events()

        print("Event Contexts: ", event_contexts)

        # Get client and lead
        try:
            client = await Client.get(ai_phone_number=community_number)
        except Exception as e:
            print(f"Error getting client: {e}")
            return {"message": "Client not found"}

        lead = None
        try:
            lead = await Lead.get(ai_phone_number=member_number, client=client)
        except Exception as e:
            print(f"Error getting lead: {e}")
            try:
                lead = await Lead.create(
                name=None,
                ai_phone_number=member_number,
                client=client
                )
                print(f"Lead created: {lead}")
            except Exception as e:
                print(f"Error creating lead: {e}")
                return {"message": "Lead not found"}
        
        # Find the conversation for this lead
        conversation = await Conversation.get_or_none(lead=lead)
        if not conversation:
            conversation = await Conversation.create(lead=lead)

        # # Extract campaign UUIDs from conversation tags
        # campaign_uuids = conversation.tags.get("campaign_uuids", []) if conversation.tags else []

        # # Aggregate full event context objects for all campaigns
        # event_contexts = []
        # for campaign_uuid in campaign_uuids:
        #     campaign = await Campaign.get_or_none(uuid=campaign_uuid)
        #     if campaign:
        #         event_name = campaign.name
        #         event_context = luma_events.get(event_name)
        #         if event_context:
        #             event_contexts.append(event_context)


        # Get next events from lu.ma
        

        # Pass the list of event context objects to the prompt template
        prompt_template = event_community_support_prompt_template(
            event_context=event_contexts,
            lead_name=lead.name if lead.name else "Unknown",
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

        # print("Messages: ", messages)

        message_history = []
        message_history.append(system_message)

        # Only include the most recent 15 messages
        recent_messages = list(messages)[-15:]
        for message in recent_messages:
            message_history.append({"role": message.role, "content": message.content})

        # for message in recent_messages:
        #     print("Role: ", message.role)
        #     print("Content: ", message.content)

        # pprint(message_history)
        
        llm_response = await call_llm(message_history)
        llm_response = json.loads(llm_response)

        # print("LLM Response: ", llm_response)

        # Save the assistant's response
        await Message.create(
            conversation=conversation,
            content=llm_response["content"],
            role="assistant"
        )

        # Send SMS back to the user
        send_sms_to_rate_limited_task.delay(
            from_number=client.ai_phone_number,
            to_number=lead.ai_phone_number,
            body=llm_response["content"]
        )

        return {"message": "SMS received"}
    except Exception as e:
        print(f"Error: {e}")
        return {"message": "Error processing webhook"}, 400


async def sms_blast_service_batch(request: SmsBlastRequest):
    # Get client
    client = await Client.get(uuid=request.client_uuid)
    campaign = await Campaign.get(uuid=request.campaign_uuid)
    results = []
    members = request.list
    batch_size = 50
    for i in range(0, len(members), batch_size):
        batch = members[i:i+batch_size]
        tasks = [
            asyncio.create_task(sms_event_invitation_task(member, campaign, client)) for member in batch
        ]
        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)
        # Sleep for 30 seconds after each batch except the last
        if i + batch_size < len(members):
            await asyncio.sleep(30)
    return results

async def sms_blast_service_batch_whatsapp_group(request: SmsBlastRequest):
    # Get client
    print("Request: ", request)
    client = await Client.get(uuid=request.client_uuid)
    campaign = await Campaign.get(uuid=request.campaign_uuid)
    results = []
    members = request.list
    batch_size = 50 
    for i in range(0, len(members), batch_size):
        batch = members[i:i+batch_size]
        tasks = [
            asyncio.create_task(sms_whatsapp_group_invitation_task(member, campaign, client)) for member in batch
        ]
        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)
        # Sleep for 30 seconds after each batch except the last
        if i + batch_size < len(members):
            await asyncio.sleep(30)
    return results

async def sms_blast_service_mass_batch(request: SmsBlastRequest):
    # Get client
    client = await Client.get(uuid=request.client_uuid)
    campaign = await Campaign.get(uuid=request.campaign_uuid)
    results = []
    # for member in request.list:
    #     result = await sms_event_invitation_task(member, campaign, client)
    #     results.append(result)

    tasks = []
    for member in request.list:
        task = asyncio.create_task(sms_event_invitation_task(member, campaign, client))
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    return results


async def sms_event_invitation_task(member_info:dict, campaign: Campaign, client: Client):
    phone_number = member_info["phone_number"]
    lead_name = member_info["name"]

    print("Phone Number: ", phone_number)
    print("Lead Name: ", lead_name)
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
        send_sms_to_rate_limited_task.delay(
            from_number=client.ai_phone_number,
            to_number=phone_number,
            body=llm_response["content"]
        )
        return {"phone_number": phone_number, "status": "sent"}
    except Exception as sms_error:
        return {"phone_number": phone_number, "status": "failed", "error": str(sms_error)}

async def sms_whatsapp_group_invitation_task(member_info:dict, campaign: Campaign, client: Client):
    phone_number = member_info["phone_number"]
    lead_name = member_info["name"]

    print("Phone Number: ", phone_number)
    print("Lead Name: ", lead_name)
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

    prompt_template = whatsapp_group_invitation_prompt_template(event_context, lead_name, gptechday_community)

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
        send_sms_to_rate_limited_task.delay(
            from_number=client.ai_phone_number,
            to_number=phone_number,
            body=llm_response["content"]
        )
        return {"phone_number": phone_number, "status": "sent"}
    except Exception as sms_error:
        return {"phone_number": phone_number, "status": "failed", "error": str(sms_error)}
