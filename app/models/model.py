from tortoise.models import Model
from tortoise import fields
import uuid
from enum import Enum
from tortoise.exceptions import ValidationError

class MessageType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PHONE_CALL = "phone_call"

class Client(Model):
    id = fields.IntField(pk=True)
    uuid = fields.UUIDField(default=uuid.uuid4)

    company_name = fields.CharField(max_length=255)
    ai_phone_number = fields.CharField(max_length=255, unique=True, null=True)
    ai_email = fields.CharField(max_length=255, unique=True, null=True)
    ai_bot_name = fields.CharField(max_length=255, null=True)

    created_at = fields.DatetimeField(auto_now_add=True, precision=6)
    updated_at = fields.DatetimeField(auto_now=True, precision=6)
    deleted_at = fields.DatetimeField(null=True, precision=6)

    class Meta:
        table = "client"

class Lead(Model):
    id = fields.IntField(pk=True)
    uuid = fields.UUIDField(default=uuid.uuid4)

    client = fields.ForeignKeyField("models.Client", related_name="lead")
    name = fields.CharField(max_length=255, null=True)
    phone_number = fields.CharField(max_length=255, null=True)
    email = fields.CharField(max_length=255, null=True)

    created_at = fields.DatetimeField(auto_now_add=True, precision=6)
    updated_at = fields.DatetimeField(auto_now=True, precision=6)
    deleted_at = fields.DatetimeField(null=True, precision=6)

    class Meta:
        table = "lead"

    async def save(self, *args, **kwargs):
        # Ensure at least one of phone_number or email is provided
        if not self.phone_number and not self.email:
            raise ValidationError(
                "At least one of 'phone_number' or 'email' must be provided."
            )
        await super().save(*args, **kwargs)


class Message(Model):
    id = fields.IntField(pk=True)
    uuid = fields.UUIDField(default=uuid.uuid4)

    conversation = fields.ForeignKeyField("models.Conversation", related_name="messages")
    content = fields.TextField()
    role = fields.CharField(max_length=255)
    message_type = fields.CharEnumField(enum_type=MessageType, null=True)

    created_at = fields.DatetimeField(auto_now_add=True, precision=6)
    updated_at = fields.DatetimeField(auto_now=True, precision=6)
    deleted_at = fields.DatetimeField(null=True, precision=6)

    class Meta:
        table = "message"

    def __str__(self):
        return self.content

class CompanyInformation(Model):
    id = fields.IntField(pk=True)
    uuid = fields.UUIDField(default=uuid.uuid4)

    client: fields.ForeignKeyNullableRelation = fields.ForeignKeyField(
        "models.Clients", related_name="company_information", on_delete=fields.CASCADE
    )
    company_name = fields.CharField(max_length=255, null=True, default=None)
    company_document = fields.TextField(null=True, default=None)
    about_us = fields.TextField(null=True, default=None)

    # Standard fields for all models
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    deleted_at = fields.DatetimeField(null=True, default=None)

    class Meta:
        table = "company_information"

class Conversation(Model):
    id = fields.IntField(pk=True)
    uuid = fields.UUIDField(default=uuid.uuid4)

    lead = fields.ForeignKeyField("models.Lead", related_name="conversations")
    campaign = fields.ForeignKeyField("models.Campaign", related_name="conversations", null=True)
    tags = fields.JSONField(null=True)

    email_message_id = fields.CharField(max_length=255, null=True, default=None)

    created_at = fields.DatetimeField(auto_now_add=True, precision=6)
    updated_at = fields.DatetimeField(auto_now=True, precision=6)
    deleted_at = fields.DatetimeField(null=True, precision=6)

    class Meta:
        table = "conversation"

    def __str__(self):
        return self.lead.name


class Campaign(Model):
    id = fields.IntField(pk=True)
    uuid = fields.UUIDField(default=uuid.uuid4)
    client = fields.ForeignKeyField("models.Client", related_name="campaigns")
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    status = fields.CharField(max_length=50, default="active")
    start_date = fields.DatetimeField(null=True)
    end_date = fields.DatetimeField(null=True)
    message_template = fields.TextField(null=True)
    leads = fields.ManyToManyField("models.Lead", related_name="campaigns", through="campaign_leads")

    created_at = fields.DatetimeField(auto_now_add=True, precision=6)
    updated_at = fields.DatetimeField(auto_now=True, precision=6)

    class Meta:
        table = "campaign"

    def __str__(self):
        return self.name