# backend/app/workers/tasks.py
import os
import sys

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.db.session import get_db_session
from app.services.enactment_service import EnactmentService
from app.utils.logging import logger

def enactment_handler(assertion_id: str):
    """
    Handle enactment processing.
    Business logic per spec section 6.4.

    This function computes the canonical digest and anchors to blockchain.

    Args:
        assertion_id: ID of the assertion to enact
    """
    logger.info(f"Enactment handler triggered for assertion: {assertion_id}")

    try:
        with get_db_session() as session:
            result = EnactmentService.enact_assertion(session, assertion_id, actor_id='worker')
            logger.info(f"Enactment completed: {result}")
            return result

    except Exception as e:
        logger.error(f"Enactment handler failed for assertion {assertion_id}: {e}")
        raise
