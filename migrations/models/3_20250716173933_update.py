from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "company_information" ADD "socials" JSONB;
        ALTER TABLE "company_information" DROP COLUMN "company_document";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "company_information" ADD "company_document" TEXT;
        ALTER TABLE "company_information" DROP COLUMN "socials";"""
