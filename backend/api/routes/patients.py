from fastapi import APIRouter, HTTPException
from config.supabase import supabase
from pydantic import BaseModel, Field
from uuid import UUID

router = APIRouter()

class PatientRequest(BaseModel):
    name: str = Field(..., min_length=1)
    age: int = Field(..., gt=0, lt=120)
    caregiver_id: UUID

@router.post("/patients")
def create_patient(data: PatientRequest):
    response = supabase.table("patients").insert({
        "name": data.name,
        "age": data.age,
        "caregiver_id": str(data.caregiver_id)
    }).execute()

    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to create patient")

    return {"data": response.data}

@router.get("/patients")
def get_patients():
    response = supabase.table("patients").select("*").execute()

    if response.data is None:
        raise HTTPException(status_code=400, detail="Failed to fetch patients")

    return {"data": response.data}