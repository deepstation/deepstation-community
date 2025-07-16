from app.models.model import CompanyInformation
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CompanyInformationRepository:
    
    @staticmethod
    async def create_company_information(
        client_id: int,
        company_name: Optional[str] = None,
        about_us: Optional[str] = None,
        socials: Optional[dict] = None,
    ):
        try:
            company_info = await CompanyInformation.create(
                client_id=client_id,
                company_name=company_name,
                about_us=about_us,
                socials=socials,
            )
            return company_info
        except Exception as error:
            print("Unable to create company information: ", error)
            logger.error("Unable to create company information: ", error)
            raise error

    @staticmethod
    async def get_company_information_by_client_id(client_id: int):
        try:
            company_info = await CompanyInformation.filter(client_id=client_id).get_or_none()
            return company_info
        except Exception as error:
            print("Unable to retrieve company information: ", error)
            logger.error("Unable to retrieve company information: ", error)
            raise error

    @staticmethod
    async def get_company_information_by_uuid(uuid: str):
        try:
            company_info = await CompanyInformation.get(uuid=uuid)
            return company_info
        except Exception as error:
            print("Unable to retrieve company information by uuid: ", error)
            logger.error("Unable to retrieve company information by uuid: ", error)
            raise error

    @staticmethod
    async def get_all_company_information():
        try:
            company_infos = await CompanyInformation.all()
            return company_infos
        except Exception as error:
            print("Unable to retrieve all company information: ", error)
            logger.error("Unable to retrieve all company information: ", error)
            raise error

    @staticmethod
    async def update_company_information(
        client_id: int,
        company_name: Optional[str] = None,
        about_us: Optional[str] = None,
        socials: Optional[dict] = None,
    ):
        try:
            update_data = {}
            if company_name is not None:
                update_data["company_name"] = company_name
            if about_us is not None:
                update_data["about_us"] = about_us
            if socials is not None:
                update_data["socials"] = socials
            
            await CompanyInformation.filter(client_id=client_id).update(**update_data)
        except Exception as error:
            print("Unable to update company information: ", error)
            logger.error("Unable to update company information: ", error)
            raise error

    @staticmethod
    async def delete_company_information(client_id: int):
        try:
            await CompanyInformation.filter(client_id=client_id).delete()
        except Exception as error:
            print("Unable to delete company information: ", error)
            logger.error("Unable to delete company information: ", error)
            raise error

    @staticmethod
    async def upsert_company_information(
        client_id: int,
        company_name: Optional[str] = None,
        about_us: Optional[str] = None,
        socials: Optional[dict] = None,
    ):
        try:
            company_info = await CompanyInformation.filter(client_id=client_id).get_or_none()
            
            if company_info:
                # Update existing
                await CompanyInformationRepository.update_company_information(
                    client_id=client_id,
                    company_name=company_name,
                    about_us=about_us,
                    socials=socials,
                )
                return await CompanyInformation.filter(client_id=client_id).get()
            else:
                # Create new
                return await CompanyInformationRepository.create_company_information(
                    client_id=client_id,
                    company_name=company_name,
                    about_us=about_us,
                    socials=socials,
                )
        except Exception as error:
            print("Unable to upsert company information: ", error)
            logger.error("Unable to upsert company information: ", error)
            raise error

    @staticmethod
    async def get_socials_by_client_id(client_id: int):
        try:
            company_info = await CompanyInformation.filter(client_id=client_id).get_or_none()
            if company_info and company_info.socials:
                return company_info.socials
            return None
        except Exception as error:
            print("Unable to retrieve socials: ", error)
            logger.error("Unable to retrieve socials: ", error)
            raise error

    @staticmethod
    async def update_socials(client_id: int, socials: dict):
        try:
            await CompanyInformation.filter(client_id=client_id).update(socials=socials)
        except Exception as error:
            print("Unable to update socials: ", error)
            logger.error("Unable to update socials: ", error)
            raise error