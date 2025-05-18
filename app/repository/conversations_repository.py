from app.models.model import Conversation, Message
from typing import List, Optional

class ConversationsRepository:
    @staticmethod
    async def create_conversation(lead_id: int) -> Conversation:
        return await Conversation.create(lead_id=lead_id)

    @staticmethod
    async def get_conversations_by_lead(lead_id: int) -> List[Conversation]:
        return await Conversation.filter(lead_id=lead_id).all()

    @staticmethod
    async def get_conversation_by_uuid(conversation_uuid: str) -> Optional[Conversation]:
        return await Conversation.get_or_none(uuid=conversation_uuid)

    @staticmethod
    async def get_messages_by_conversation(conversation_id: int) -> List[Message]:
        return await Message.filter(conversation_id=conversation_id).all()
