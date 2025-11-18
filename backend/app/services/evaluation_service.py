# backend/app/services/evaluation_service.py
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException
from redis import Redis
from rq import Queue
import os
import uuid

from ..db import crud
from ..db.models import ClaimStatus
from ..schemas.evaluation import EvaluationCreate, EvaluationResponse
from ..utils.canonicalize import canonicalize_evaluation
from ..utils.crypto import verify_signature
from ..utils.logging import logger

# Redis connection for job queue
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_conn = Redis.from_url(REDIS_URL)
job_queue = Queue('default', connection=redis_conn)

class EvaluationService:
    @staticmethod
    def create_evaluation(db: Session, assertion_id: str, evaluation_data: EvaluationCreate) -> dict:
        """
        Create evaluation with all business rules.
        Business logic per spec section 6.2.
        """
        # 1. Get assertion with row lock
        assertion = crud.get_assertion_for_update(db, assertion_id)
        if not assertion:
            raise HTTPException(status_code=404, detail="Assertion not found")

        # 2. Get evaluator agent
        evaluator = crud.get_agent(db, evaluation_data.agent_id)
        if not evaluator:
            raise HTTPException(status_code=400, detail="Evaluator agent not found")

        # 3. Validate evaluator != asserter (C2 constraint)
        if evaluation_data.agent_id == assertion.agent_id:
            raise HTTPException(status_code=409, detail="Evaluator cannot be the same as asserter (C2 violation)")

        # 4. Get schema and validate evaluator role
        schema = crud.get_schema(db, assertion.schema_id)
        if evaluator.role != schema.required_role:
            raise HTTPException(
                status_code=403,
                detail=f"Evaluator role {evaluator.role.value} does not match required role {schema.required_role.value}"
            )

        # 5. Check deadline
        deadline_seconds = schema.deadline_hours * 3600
        time_elapsed = (datetime.utcnow() - assertion.timestamp).total_seconds()

        if time_elapsed > deadline_seconds:
            # Assertion has timed out
            crud.update_assertion_status(db, assertion_id, ClaimStatus.TIMED_OUT)
            crud.create_audit_log(db, 'system', 'assertion_timed_out', {
                'assertion_id': assertion_id,
                'time_elapsed': time_elapsed,
                'deadline': deadline_seconds
            })
            raise HTTPException(status_code=410, detail="Assertion has timed out; deadline exceeded")

        # 6. Validate signature if provided
        if evaluation_data.signature:
            canonical_data = canonicalize_evaluation({
                'id': evaluation_data.id,
                'assertion_id': assertion_id,
                'agent_id': evaluation_data.agent_id,
                'timestamp': evaluation_data.timestamp or datetime.utcnow(),
                'result': evaluation_data.result,
                'notes': evaluation_data.notes
            })

            if not verify_signature(canonical_data, evaluation_data.signature, evaluator.public_key):
                raise HTTPException(status_code=401, detail="Invalid signature")

        # 7. Create evaluation record
        db_evaluation = crud.create_evaluation(db, {
            'id': evaluation_data.id,
            'assertion_id': assertion_id,
            'agent_id': evaluation_data.agent_id,
            'timestamp': evaluation_data.timestamp or datetime.utcnow(),
            'result': evaluation_data.result,
            'notes': evaluation_data.notes,
            'signature': evaluation_data.signature
        })

        enactment_id = None

        # 8. Process evaluation result
        if evaluation_data.result:
            # VERIFIED - Create enactment
            crud.update_assertion_status(db, assertion_id, ClaimStatus.VERIFIED)

            # Create enactment record
            enactment_id = f"enactment-{uuid.uuid4()}"
            db_enactment = crud.create_enactment(db, {
                'id': enactment_id,
                'assertion_id': assertion_id,
                'timestamp': datetime.utcnow(),
                'enacted_by': 'system',
                'metadata': {
                    'evaluation_id': evaluation_data.id,
                    'evaluator_id': evaluation_data.agent_id
                }
            })

            # Enqueue enactment worker job with assertion_id
            try:
                job_queue.enqueue(
                    'app.workers.tasks.enactment_handler',
                    assertion_id
                )
                logger.info(f"Enqueued enactment job for assertion {assertion_id}, enactment {enactment_id}")
            except Exception as e:
                logger.error(f"Failed to enqueue enactment job: {e}")

            crud.create_audit_log(db, evaluation_data.agent_id, 'assertion_verified', {
                'assertion_id': assertion_id,
                'evaluation_id': evaluation_data.id,
                'enactment_id': enactment_id
            })

        else:
            # REJECTED
            crud.update_assertion_status(db, assertion_id, ClaimStatus.REJECTED)

            # Apply fallback logic (could include batch downgrade, notifications, etc.)
            logger.info(f"Assertion {assertion_id} rejected by {evaluation_data.agent_id}")

            crud.create_audit_log(db, evaluation_data.agent_id, 'assertion_rejected', {
                'assertion_id': assertion_id,
                'evaluation_id': evaluation_data.id,
                'notes': evaluation_data.notes
            })

        # Commit transaction
        db.commit()

        return {
            "id": db_evaluation.id,
            "assertion_id": assertion_id,
            "status": assertion.status.value,
            "enactment_id": enactment_id
        }
