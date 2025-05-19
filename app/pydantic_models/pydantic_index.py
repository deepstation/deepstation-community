from typing import List, Dict

from pydantic import BaseModel


class SendSmsRequest(BaseModel):
    lead_uuid: str
    client_uuid: str
    time_of_call: str
    
class SmsBlastRequest(BaseModel):
    list: List[Dict[str, str]]
    campaign_uuid: str
    client_uuid: str