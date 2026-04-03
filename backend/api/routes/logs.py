from fastapi import APIRouter, HTTPException
from config.supabase import supabase
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Literal

router = APIRouter()

class LogRequest(BaseModel):
    patient_id: str
    session: Literal["MORNING", "AFTERNOON", "NIGHT"]
    status: Literal["VERIFIED", "MISSED", "PENDING"]

@router.post("/log-intake")
def log_intake(data: LogRequest):
    response = supabase.table("dose_logs").insert({
        "patient_id": data.patient_id,
        "session": data.session,
        "status": data.status,
        "verified_at": datetime.now(timezone.utc).isoformat()
    }).execute()

    if not response.data:
        raise HTTPException(status_code=400, detail="Failed to insert log")

    return {"data": response.data}

@router.get("/logs/{patient_id}")
def get_logs(patient_id: str):
    response = supabase.table("dose_logs") \
        .select("*") \
        .eq("patient_id", patient_id) \
        .order("verified_at", desc=True) \
        .execute()

    if response.data is None:
        raise HTTPException(status_code=400, detail="Failed to fetch logs")

    return {"data": response.data}