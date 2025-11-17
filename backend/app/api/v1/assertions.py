# backend/app/api/v1/assertions.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ...db.session import get_db
from ...schemas.assertion import AssertionCreate, AssertionResponse, AssertionStatusResponse
from ...services.assertion_service import AssertionService

router = APIRouter()

@router.post("", status_code=201)
def create_assertion(
    assertion_data: AssertionCreate,
    db: Session = Depends(get_db)
):
    """
    Create new assertion with signature validation and TTL scheduling.

    Request body:
    - id: Unique assertion ID
    - batch_id: Product batch ID
    - agent_id: Agent making the assertion
    - schema_id: Schema ID defining the assertion type
    - timestamp: Optional timestamp (defaults to now)
    - location_gps: Optional GPS coordinates
    - content_data: JSON content (e.g., {"score": 95, "moisture": "11%"})
    - signature: Optional cryptographic signature

    Response:
    - id: Assertion ID
    - status: Current status (pending)
    - message: Confirmation message
    """
    return AssertionService.create_assertion(db, assertion_data)

@router.get("", response_model=List[AssertionResponse])
def get_assertions(
    status: str = "pending",
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get assertions by status.

    Query params:
    - status: Filter by status (pending, verified, rejected, timed_out, enacted)
    - limit: Max number of results (default 100)
    """
    return AssertionService.get_pending_assertions(db, limit)

@router.get("/{assertion_id}/status", response_model=AssertionStatusResponse)
def get_assertion_status(
    assertion_id: str,
    db: Session = Depends(get_db)
):
    """
    Get assertion status with deadline information.

    Response includes:
    - id: Assertion ID
    - status: Current status
    - deadline_seconds: Total deadline in seconds
    - time_elapsed_seconds: Time elapsed since assertion creation
    - is_near_deadline: Boolean indicating if near deadline (< 10% remaining)
    """
    return AssertionService.get_assertion_status(db, assertion_id)
