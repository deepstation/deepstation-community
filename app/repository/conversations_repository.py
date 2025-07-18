from app.models.model import Conversation, Message, MessageType
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

    @staticmethod
    async def create_user_message(conversation_id: str, content: str, medium_response_type: str) -> Message:
        """Create a user message in a conversation"""
        # Convert medium_response_type to MessageType enum
        message_type = MessageType.EMAIL if medium_response_type == "email" else MessageType.SMS
        
        return await Message.create(
            conversation_id=int(conversation_id),
            content=content,
            role="user",
            message_type=message_type
        )

    @staticmethod
    async def create_assistant_message(
        conversation_id: str, 
        content: str, 
        medium_response_type: str,
        message_id: Optional[str] = None,
        in_reply_to: Optional[str] = None,
        references: Optional[list] = None,
        from_addr: Optional[str] = None,
        to_addr: Optional[str] = None,
        subject: Optional[str] = None,
        email_date: Optional[str] = None
    ) -> Message:
        try:
            """Create an assistant message in a conversation"""
            # Convert medium_response_type to MessageType enum
            message_type = MessageType.EMAIL if medium_response_type == "email" else MessageType.SMS
            
            return await Message.create(
                conversation_id=int(conversation_id),
                content=content,
                role="assistant",
                message_type=message_type,
                message_id=message_id,
                in_reply_to=in_reply_to,
                references=references,
                from_addr=from_addr,
                to_addr=to_addr,
                subject=subject,
                email_date=email_date
            )
        except Exception as e:
            print("Conversation Repository error: ", e)
            raise
