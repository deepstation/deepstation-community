from tortoise.models import Model
from tortoise import fields
import uuid

class Client(Model):
    id = fields.IntField(pk=True)
    uuid = fields.UUIDField(default=uuid.uuid4)

    name = fields.CharField(max_length=255)
    ai_phone_number = fields.CharField(max_length=255, unique=True)
    ai_bot_name = fields.CharField(max_length=255)

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
    ai_phone_number = fields.CharField(max_length=255, unique=True)
    
    created_at = fields.DatetimeField(auto_now_add=True, precision=6)
    updated_at = fields.DatetimeField(auto_now=True, precision=6)
    deleted_at = fields.DatetimeField(null=True, precision=6)

    class Meta:
        table = "lead"

class Message(Model):
    id = fields.IntField(pk=True)
    uuid = fields.UUIDField(default=uuid.uuid4)

    conversation = fields.ForeignKeyField("models.Conversation", related_name="messages")
    content = fields.TextField()
    role = fields.CharField(max_length=255)
    message_type = fields.CharField(max_length=255, null=True)

    created_at = fields.DatetimeField(auto_now_add=True, precision=6)
    updated_at = fields.DatetimeField(auto_now=True, precision=6)
    deleted_at = fields.DatetimeField(null=True, precision=6)

    class Meta:
        table = "message"

    def __str__(self):
        return self.content

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

class Conversation(Model):
    id = fields.IntField(pk=True)
    uuid = fields.UUIDField(default=uuid.uuid4)

    lead = fields.ForeignKeyField("models.Lead", related_name="conversations")
    campaign = fields.ForeignKeyField("models.Campaign", related_name="conversations", null=True)
    tags = fields.JSONField(null=True)

    created_at = fields.DatetimeField(auto_now_add=True, precision=6)
    updated_at = fields.DatetimeField(auto_now=True, precision=6)
    deleted_at = fields.DatetimeField(null=True, precision=6)

    class Meta:
        table = "conversation"

    def __str__(self):
        return self.lead.name
