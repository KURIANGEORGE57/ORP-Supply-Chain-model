# backend/app/schemas/evaluation.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EvaluationCreate(BaseModel):
    id: str
    agent_id: str
    timestamp: Optional[datetime] = None
    result: bool
    notes: Optional[str] = None
    signature: Optional[str] = None

class EvaluationResponse(BaseModel):
    id: str
    assertion_id: str
    agent_id: str
    timestamp: datetime
    result: bool
    notes: Optional[str]
    status: str
    enactment_id: Optional[str] = None

    class Config:
        from_attributes = True
