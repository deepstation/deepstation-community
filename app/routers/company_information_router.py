from fastapi import APIRouter, HTTPException
from app.repository.company_information_repository import CompanyInformationRepository
import pydantic
from typing import Optional
from app.models.model import Client
class CreateCompanyInformationRequest(pydantic.BaseModel):
    client_uuid: str
    company_name: Optional[str] = None
    about_us: Optional[str] = None
    socials: Optional[dict] = None

class UpdateCompanyInformationRequest(pydantic.BaseModel):
    client_uuid: str
    company_name: Optional[str] = None
    about_us: Optional[str] = None
    socials: Optional[dict] = None

class UpsertCompanyInformationRequest(pydantic.BaseModel):
    client_uuid: str
    company_name: Optional[str] = None
    about_us: Optional[str] = None
    socials: Optional[dict] = None

class UpdateSocialsRequest(pydantic.BaseModel):
    client_uuid: str
    socials: Optional[dict] = None

company_information_router = APIRouter()

@company_information_router.post("/api/company-information/create")
async def create_company_information(request: CreateCompanyInformationRequest):
    try:
        client = await Client.filter(uuid=request.client_uuid).get_or_none()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        client_id = client.id
        company_info = await CompanyInformationRepository.create_company_information(
            client_id=client_id,
            company_name=request.company_name,
            about_us=request.about_us,
            socials=request.socials
        )
        return {"message": "Company information created successfully", "uuid": str(company_info.uuid)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@company_information_router.get("/api/company-information/client/{client_id}")
async def get_company_information_by_client_id(client_id: int):
    try:
        company_info = await CompanyInformationRepository.get_company_information_by_client_id(client_id)
        if not company_info:
            raise HTTPException(status_code=404, detail="Company information not found")
        return company_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@company_information_router.get("/api/company-information/uuid/{uuid}")
async def get_company_information_by_uuid(uuid: str):
    try:
        company_info = await CompanyInformationRepository.get_company_information_by_uuid(uuid)
        return company_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@company_information_router.get("/api/company-information/all")
async def get_all_company_information():
    try:
        company_infos = await CompanyInformationRepository.get_all_company_information()
        return company_infos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@company_information_router.put("/api/company-information/client/{client_id}")
async def update_company_information(client_id: int, request: UpdateCompanyInformationRequest):
    try:
        await CompanyInformationRepository.update_company_information(
            client_id=client_id,
            company_name=request.company_name,
            about_us=request.about_us,
            socials=request.socials
        )
        return {"message": "Company information updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@company_information_router.delete("/api/company-information/client/{client_id}")
async def delete_company_information(client_id: int):
    try:
        await CompanyInformationRepository.delete_company_information(client_id)
        return {"message": "Company information deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@company_information_router.post("/api/company-information/upsert")
async def upsert_company_information(request: UpsertCompanyInformationRequest):
    try:
        company_info = await CompanyInformationRepository.upsert_company_information(
            client_id=request.client_id,
            company_name=request.company_name,
            about_us=request.about_us,
            socials=request.socials
        )
        return {"message": "Company information upserted successfully", "uuid": str(company_info.uuid)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@company_information_router.get("/api/company-information/socials/{client_id}")
async def get_socials_by_client_id(client_id: int):
    try:
        socials = await CompanyInformationRepository.get_socials_by_client_id(client_id)
        if socials is None:
            raise HTTPException(status_code=404, detail="Socials not found")
        return {"socials": socials}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@company_information_router.put("/api/company-information/socials/{client_id}")
async def update_socials(client_id: int, request: UpdateSocialsRequest):
    try:
        await CompanyInformationRepository.update_socials(client_id, request.socials)
        return {"message": "Socials updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))