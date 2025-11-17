# backend/app/schemas/assertion.py
from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime

class AssertionCreate(BaseModel):
    id: str
    batch_id: str
    agent_id: str
    schema_id: str
    timestamp: Optional[datetime] = None
    location_gps: Optional[str] = None
    content_data: Dict
    signature: Optional[str] = None

class AssertionResponse(BaseModel):
    id: str
    batch_id: str
    agent_id: str
    schema_id: str
    timestamp: datetime
    location_gps: Optional[str]
    content_data: Dict
    status: str

    class Config:
        from_attributes = True

class AssertionStatusResponse(BaseModel):
    id: str
    status: str
    deadline_seconds: int
    time_elapsed_seconds: int
    is_near_deadline: bool
