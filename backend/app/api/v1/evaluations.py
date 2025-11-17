# backend/app/api/v1/evaluations.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...schemas.evaluation import EvaluationCreate, EvaluationResponse
from ...services.evaluation_service import EvaluationService

router = APIRouter()

@router.post("/assertions/{assertion_id}/evaluations", status_code=200)
def create_evaluation(
    assertion_id: str,
    evaluation_data: EvaluationCreate,
    db: Session = Depends(get_db)
):
    """
    Create evaluation for an assertion.

    Path params:
    - assertion_id: ID of the assertion being evaluated

    Request body:
    - id: Unique evaluation ID
    - agent_id: Evaluator agent ID
    - timestamp: Optional timestamp (defaults to now)
    - result: Boolean - true for approve, false for reject
    - notes: Optional notes explaining the evaluation
    - signature: Optional cryptographic signature

    Response:
    - id: Evaluation ID
    - assertion_id: Assertion ID
    - status: Updated assertion status
    - enactment_id: ID of enactment if created (when result=true)

    Error codes:
    - 400: Invalid request
    - 401: Invalid signature
    - 403: Evaluator role does not match required role
    - 404: Assertion not found
    - 409: Evaluator is same as asserter (C2 violation)
    - 410: Assertion has timed out
    """
    return EvaluationService.create_evaluation(db, assertion_id, evaluation_data)
