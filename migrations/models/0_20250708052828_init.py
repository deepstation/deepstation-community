from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "client" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "uuid" UUID NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "ai_phone_number" VARCHAR(255) NOT NULL UNIQUE,
    "ai_bot_name" VARCHAR(255) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "deleted_at" TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS "campaign" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "uuid" UUID NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "description" TEXT,
    "status" VARCHAR(50) NOT NULL DEFAULT 'active',
    "start_date" TIMESTAMPTZ,
    "end_date" TIMESTAMPTZ,
    "message_template" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "client_id" INT NOT NULL REFERENCES "client" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "lead" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "uuid" UUID NOT NULL,
    "name" VARCHAR(255),
    "ai_phone_number" VARCHAR(255) NOT NULL UNIQUE,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "deleted_at" TIMESTAMPTZ,
    "client_id" INT NOT NULL REFERENCES "client" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "conversation" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "uuid" UUID NOT NULL,
    "tags" JSONB,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "deleted_at" TIMESTAMPTZ,
    "campaign_id" INT REFERENCES "campaign" ("id") ON DELETE CASCADE,
    "lead_id" INT NOT NULL REFERENCES "lead" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "message" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "uuid" UUID NOT NULL,
    "content" TEXT NOT NULL,
    "role" VARCHAR(255) NOT NULL,
    "message_type" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "deleted_at" TIMESTAMPTZ,
    "conversation_id" INT NOT NULL REFERENCES "conversation" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "campaign_leads" (
    "campaign_id" INT NOT NULL REFERENCES "campaign" ("id") ON DELETE CASCADE,
    "lead_id" INT NOT NULL REFERENCES "lead" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_campaign_le_campaig_9e6f9e" ON "campaign_leads" ("campaign_id", "lead_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
