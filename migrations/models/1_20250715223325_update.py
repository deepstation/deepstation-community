from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "uid_lead_ai_phon_1d958c";
        ALTER TABLE "client" ADD "ai_email" VARCHAR(255) UNIQUE;
        ALTER TABLE "client" RENAME COLUMN "name" TO "company_name";
        ALTER TABLE "client" ALTER COLUMN "ai_bot_name" DROP NOT NULL;
        ALTER TABLE "client" ALTER COLUMN "ai_phone_number" DROP NOT NULL;
        CREATE TABLE IF NOT EXISTS "company_information" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "uuid" UUID NOT NULL,
    "company_name" VARCHAR(255),
    "company_document" TEXT,
    "about_us" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "deleted_at" TIMESTAMPTZ,
    "client_id" INT NOT NULL REFERENCES "client" ("id") ON DELETE CASCADE
);
        ALTER TABLE "conversation" ADD "email_message_id" VARCHAR(255);
        ALTER TABLE "lead" ADD "email" VARCHAR(255);
        ALTER TABLE "lead" ADD "phone_number" VARCHAR(255);
        ALTER TABLE "lead" DROP COLUMN "ai_phone_number";
        ALTER TABLE "message" ALTER COLUMN "message_type" TYPE VARCHAR(10) USING "message_type"::VARCHAR(10);
        COMMENT ON COLUMN "message"."message_type" IS 'EMAIL: email
SMS: sms
PHONE_CALL: phone_call';
        CREATE UNIQUE INDEX IF NOT EXISTS "uid_client_ai_emai_08eac2" ON "client" ("ai_email");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "uid_client_ai_emai_08eac2";
        ALTER TABLE "lead" ADD "ai_phone_number" VARCHAR(255) NOT NULL UNIQUE;
        ALTER TABLE "lead" DROP COLUMN "email";
        ALTER TABLE "lead" DROP COLUMN "phone_number";
        ALTER TABLE "client" RENAME COLUMN "company_name" TO "name";
        ALTER TABLE "client" DROP COLUMN "ai_email";
        ALTER TABLE "client" ALTER COLUMN "ai_bot_name" SET NOT NULL;
        ALTER TABLE "client" ALTER COLUMN "ai_phone_number" SET NOT NULL;
        ALTER TABLE "message" ALTER COLUMN "message_type" TYPE VARCHAR(255) USING "message_type"::VARCHAR(255);
        COMMENT ON COLUMN "message"."message_type" IS NULL;
        ALTER TABLE "conversation" DROP COLUMN "email_message_id";
        DROP TABLE IF EXISTS "company_information";
        CREATE UNIQUE INDEX IF NOT EXISTS "uid_lead_ai_phon_1d958c" ON "lead" ("ai_phone_number");"""
