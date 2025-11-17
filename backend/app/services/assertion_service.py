# backend/app/services/assertion_service.py
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from fastapi import HTTPException
from redis import Redis
from rq import Queue
import os

from ..db import crud
from ..db.models import ClaimStatus
from ..schemas.assertion import AssertionCreate, AssertionResponse, AssertionStatusResponse
from ..utils.canonicalize import canonicalize_assertion
from ..utils.crypto import verify_signature
from ..utils.logging import logger

# Redis connection for job queue
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_conn = Redis.from_url(REDIS_URL)
job_queue = Queue('default', connection=redis_conn)

class AssertionService:
    @staticmethod
    def create_assertion(db: Session, assertion_data: AssertionCreate) -> dict:
        """
        Create new assertion with signature validation and TTL scheduling.
        Business logic per spec section 6.1.
        """
        # 1. Validate agent exists
        agent = crud.get_agent(db, assertion_data.agent_id)
        if not agent:
            raise HTTPException(status_code=400, detail="Agent not found")

        # 2. Validate schema exists
        schema = crud.get_schema(db, assertion_data.schema_id)
        if not schema:
            raise HTTPException(status_code=400, detail="Schema not found")

        # 3. Validate batch exists
        batch = crud.get_product_batch(db, assertion_data.batch_id)
        if not batch:
            raise HTTPException(status_code=400, detail="Product batch not found")

        # 4. Validate signature if provided
        if assertion_data.signature:
            canonical_data = canonicalize_assertion({
                'id': assertion_data.id,
                'batch_id': assertion_data.batch_id,
                'agent_id': assertion_data.agent_id,
                'schema_id': assertion_data.schema_id,
                'timestamp': assertion_data.timestamp or datetime.utcnow(),
                'location_gps': assertion_data.location_gps,
                'content_data': assertion_data.content_data
            })

            if not verify_signature(canonical_data, assertion_data.signature, agent.public_key):
                raise HTTPException(status_code=401, detail="Invalid signature")

        # 5. Create assertion in database
        db_assertion = crud.create_assertion(db, {
            'id': assertion_data.id,
            'batch_id': assertion_data.batch_id,
            'agent_id': assertion_data.agent_id,
            'schema_id': assertion_data.schema_id,
            'timestamp': assertion_data.timestamp or datetime.utcnow(),
            'location_gps': assertion_data.location_gps,
            'content_data': assertion_data.content_data,
            'status': ClaimStatus.PENDING,
            'signature': assertion_data.signature
        })

        # 6. Schedule TTL deadline
        deadline_seconds = schema.deadline_hours * 3600
        try:
            # Schedule TTL timeout job
            job_queue.enqueue_in(
                timedelta(seconds=deadline_seconds),
                'app.workers.ttl_worker.ttl_handler',
                assertion_data.id
            )
            logger.info(f"Scheduled TTL for assertion {assertion_data.id}, deadline: {deadline_seconds}s")
        except Exception as e:
            logger.error(f"Failed to schedule TTL: {e}")
            # Continue - TTL scheduling failure shouldn't block assertion creation

        # 7. Create audit log
        crud.create_audit_log(db, assertion_data.agent_id, 'assertion_created', {
            'assertion_id': assertion_data.id,
            'batch_id': assertion_data.batch_id,
            'schema_id': assertion_data.schema_id
        })

        return {
            "id": db_assertion.id,
            "status": db_assertion.status.value,
            "message": "Assertion created; deadline scheduled"
        }

    @staticmethod
    def get_assertion_status(db: Session, assertion_id: str) -> AssertionStatusResponse:
        """Get assertion status with deadline information."""
        assertion = crud.get_assertion(db, assertion_id)
        if not assertion:
            raise HTTPException(status_code=404, detail="Assertion not found")

        schema = crud.get_schema(db, assertion.schema_id)
        deadline_seconds = schema.deadline_hours * 3600

        # Calculate elapsed time
        time_elapsed = (datetime.utcnow() - assertion.timestamp).total_seconds()
        time_remaining = max(0, deadline_seconds - time_elapsed)

        # Check if near deadline (< 10% time remaining)
        is_near_deadline = time_remaining < (deadline_seconds * 0.1)

        return AssertionStatusResponse(
            id=assertion.id,
            status=assertion.status.value,
            deadline_seconds=deadline_seconds,
            time_elapsed_seconds=int(time_elapsed),
            is_near_deadline=is_near_deadline
        )

    @staticmethod
    def get_pending_assertions(db: Session, limit: int = 100) -> list:
        """Get all pending assertions."""
        assertions = crud.get_assertions_by_status(db, ClaimStatus.PENDING, limit)
        return [
            AssertionResponse(
                id=a.id,
                batch_id=a.batch_id,
                agent_id=a.agent_id,
                schema_id=a.schema_id,
                timestamp=a.timestamp,
                location_gps=a.location_gps,
                content_data=a.content_data,
                status=a.status.value
            ) for a in assertions
        ]
