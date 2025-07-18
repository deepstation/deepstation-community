from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "message" ADD "message_id" VARCHAR(255) UNIQUE;
        ALTER TABLE "message" ADD "email_date" TIMESTAMPTZ;
        ALTER TABLE "message" ADD "references" JSONB;
        ALTER TABLE "message" ADD "to_addr" VARCHAR(255);
        ALTER TABLE "message" ADD "in_reply_to" VARCHAR(255);
        ALTER TABLE "message" ADD "from_addr" VARCHAR(255);
        ALTER TABLE "message" ADD "subject" VARCHAR(998);
        CREATE UNIQUE INDEX IF NOT EXISTS "uid_message_message_4b7652" ON "message" ("message_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "uid_message_message_4b7652";
        ALTER TABLE "message" DROP COLUMN "message_id";
        ALTER TABLE "message" DROP COLUMN "email_date";
        ALTER TABLE "message" DROP COLUMN "references";
        ALTER TABLE "message" DROP COLUMN "to_addr";
        ALTER TABLE "message" DROP COLUMN "in_reply_to";
        ALTER TABLE "message" DROP COLUMN "from_addr";
        ALTER TABLE "message" DROP COLUMN "subject";"""
