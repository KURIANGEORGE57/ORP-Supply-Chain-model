# backend/app/workers/ttl_worker.py
import os
import sys

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from redis import Redis
from rq import Queue, Worker, Connection
from app.db.session import get_db_session
from app.db import crud
from app.utils.logging import logger

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_conn = Redis.from_url(REDIS_URL)
job_queue = Queue('default', connection=redis_conn)

def ttl_handler(assertion_id: str):
    """
    Handle TTL expiry for an assertion.
    Business logic per spec section 6.3.

    This function is idempotent and safe to run multiple times.
    """
    logger.info(f"TTL handler triggered for assertion: {assertion_id}")

    with get_db_session() as session:
        # Get assertion with row lock
        assertion = crud.get_assertion_for_update(session, assertion_id)

        if not assertion:
            logger.warning(f"Assertion {assertion_id} not found")
            return

        # Only process if still pending
        if assertion.status.value != 'pending':
            logger.info(f"Assertion {assertion_id} status is {assertion.status.value}, skipping timeout")
            return

        # Mark as timed out
        crud.mark_assertion_timed_out(session, assertion_id)
        logger.info(f"Marked assertion {assertion_id} as TIMED_OUT")

        # Apply fallback actions (e.g., batch quality downgrade)
        # For MVP, just log the event
        batch = crud.get_product_batch(session, assertion.batch_id)
        if batch:
            logger.info(f"Batch {batch.batch_id} assertion timed out - may require quality downgrade")

        # Create audit log
        crud.create_audit_log(
            session,
            actor_id='system',
            action='assertion_timed_out',
            payload={
                'assertion_id': assertion_id,
                'batch_id': assertion.batch_id,
                'schema_id': assertion.schema_id
            }
        )

        # TODO: Send notifications (email, websocket, etc.)

        session.commit()
        logger.info(f"TTL timeout processing complete for {assertion_id}")

if __name__ == "__main__":
    logger.info("Starting RQ worker for TTL processing...")
    with Connection(redis_conn):
        worker = Worker(['default'])
        worker.work()
