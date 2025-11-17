# backend/app/services/enactment_service.py
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException

from ..db import crud
from ..db.models import ClaimStatus
from ..utils.canonicalize import compute_enactment_digest
from ..utils.logging import logger

class EnactmentService:
    @staticmethod
    def enact_assertion(db: Session, enactment_id: str, actor_id: str = 'worker') -> dict:
        """
        Perform enactment: compute digest and optionally anchor to blockchain.
        Business logic per spec section 6.4.
        """
        # 1. Get enactment record
        enactment = crud.get_enactment_by_assertion(db, enactment_id)
        if not enactment:
            # Try getting by enactment ID directly
            enactment = db.query(crud.Enactment).filter(crud.Enactment.id == enactment_id).first()

        if not enactment:
            raise HTTPException(status_code=404, detail="Enactment not found")

        # 2. Get assertion and evaluation
        assertion = crud.get_assertion(db, enactment.assertion_id)
        if not assertion:
            raise HTTPException(status_code=404, detail="Assertion not found")

        evaluation = crud.get_evaluation_by_assertion(db, enactment.assertion_id)
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")

        # 3. Compute canonical digest
        assertion_data = {
            'id': assertion.id,
            'batch_id': assertion.batch_id,
            'agent_id': assertion.agent_id,
            'schema_id': assertion.schema_id,
            'timestamp': assertion.timestamp.isoformat(),
            'location_gps': assertion.location_gps,
            'content_data': assertion.content_data
        }

        evaluation_data = {
            'id': evaluation.id,
            'assertion_id': evaluation.assertion_id,
            'agent_id': evaluation.agent_id,
            'timestamp': evaluation.timestamp.isoformat(),
            'result': evaluation.result
        }

        metadata = enactment.metadata or {}

        digest = compute_enactment_digest(assertion_data, evaluation_data, metadata)

        # 4. Simulate blockchain anchor (for demo/MVP)
        # In production, this would submit to Hyperledger Fabric, Ethereum L2, etc.
        blockchain_hash = f"0x{digest[:40]}"  # Simulated tx hash
        logger.info(f"Simulated blockchain anchor: {blockchain_hash}")

        # 5. Update enactment with blockchain hash
        crud.update_enactment_hash(db, enactment.id, blockchain_hash)

        # 6. Update assertion status to ENACTED
        crud.update_assertion_status(db, assertion.id, ClaimStatus.ENACTED)

        # 7. Update product batch custodian if needed (custody transfer logic)
        # This is simplified - in production would have more complex custody rules
        batch = crud.get_product_batch(db, assertion.batch_id)
        if batch:
            # For now, keep current custodian
            pass

        # 8. Create audit log
        crud.create_audit_log(db, actor_id, 'assertion_enacted', {
            'assertion_id': assertion.id,
            'enactment_id': enactment.id,
            'blockchain_hash': blockchain_hash,
            'digest': digest
        })

        db.commit()

        return {
            "enactment_id": enactment.id,
            "blockchain_hash": blockchain_hash,
            "timestamp": enactment.timestamp
        }
