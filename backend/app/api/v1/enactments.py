# backend/app/api/v1/enactments.py
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...schemas.enactment import EnactmentCreate, EnactmentResponse
from ...services.enactment_service import EnactmentService
from ...core.config import settings

router = APIRouter()

def verify_service_token(x_service_token: str = Header(...)):
    """Verify service token for worker-to-backend communication."""
    if x_service_token != settings.SERVICE_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid service token")
    return True

@router.post("/assertions/{assertion_id}/enact", response_model=EnactmentResponse)
def enact_assertion(
    assertion_id: str,
    enactment_data: EnactmentCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_service_token)
):
    """
    Enact an assertion (worker-only endpoint).

    Protected by service token in X-Service-Token header.

    Path params:
    - assertion_id: ID of the assertion to enact

    Request body:
    - actor_id: ID of the actor performing enactment (usually 'worker' or 'admin')

    Response:
    - enactment_id: ID of the enactment
    - blockchain_hash: Blockchain transaction hash (or simulated hash for demo)
    - timestamp: Enactment timestamp
    """
    return EnactmentService.enact_assertion(db, assertion_id, enactment_data.actor_id)
