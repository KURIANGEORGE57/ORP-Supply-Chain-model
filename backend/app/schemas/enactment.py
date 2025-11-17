# backend/app/schemas/enactment.py
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class EnactmentCreate(BaseModel):
    actor_id: str

class EnactmentResponse(BaseModel):
    enactment_id: str
    blockchain_hash: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True
