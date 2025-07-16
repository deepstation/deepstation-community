import httpx
from datetime import datetime, timezone
import os

LUMA_API_KEY = os.getenv("LUMA_API_KEY")
LUMA_LIST_EVENTS_URL = "https://public-api.lu.ma/public/v1/calendar/list-events"


async def fetch_luma_events() -> list[dict]:
    """
    Fetch upcoming events from the Luma calendar.
    We first pull all events (API already limits default page size).
    Then we keep only those whose start time is in the future.
    Returns minimal fields for the prompt template.
    """
    now_utc = datetime.now(timezone.utc)

    headers = {
        "accept": "application/json",
        "x-luma-api-key": LUMA_API_KEY,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(LUMA_LIST_EVENTS_URL, headers=headers)
        response.raise_for_status()
        raw = response.json()

    # print("Raw: ", raw)

    # Use the correct key for events
    events_raw = raw.get("entries") or raw.get("items") or raw.get("events") or raw.get("data") or []

    # If it's not a list yet but a dict, attempt deeper extraction
    if isinstance(events_raw, dict):
        if "entries" in events_raw:
            events_raw = events_raw["entries"]
        elif "items" in events_raw:
            events_raw = events_raw["items"]
        elif "events" in events_raw:
            events_raw = events_raw["events"]
        else:
            events_raw = []

    event_contexts: list[dict] = []
    for ev in events_raw:
        event_data = ev.get('event', ev)  # Use ev['event'] if present, else ev
        start_raw = (
            event_data.get("start_time") or
            event_data.get("startTime") or
            event_data.get("start_at") or
            event_data.get("start")
        )
        try:
            start_dt = datetime.fromisoformat(start_raw.replace("Z", "+00:00")) if start_raw else None
        except Exception:
            start_dt = None

        if start_dt and start_dt < now_utc:
            continue

        # Extract address and city if available
        address = None
        city = None
        geo = event_data.get("geo_address_json")
        if geo:
            address = geo.get("full_address") or geo.get("address")
            city = geo.get("city")

        event_contexts.append({
            "id": event_data.get("id") or event_data.get("api_id") or event_data.get("event_id"),
            "name": event_data.get("title") or event_data.get("name"),
            "start_time": start_raw,
            "timezone": event_data.get("timezone") or event_data.get("time_zone"),
            "url": event_data.get("url") or event_data.get("event_url") or event_data.get("public_url"),
            "description": event_data.get("description") or event_data.get("summary"),
            "address": address,
            "city": city,
        })

    if not event_contexts:
        print("[fetch_luma_events] No upcoming events found or parsing failed.")

    return event_contexts
