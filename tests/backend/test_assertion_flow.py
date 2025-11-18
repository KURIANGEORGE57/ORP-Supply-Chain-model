"""
Tests for assertion flow as specified in section 11 of the blueprint.
"""
import pytest
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend')))

from app.db.session import SessionLocal
from app.db import crud
from app.db.models import RoleType, ClaimStatus
from app.services.assertion_service import AssertionService
from app.services.evaluation_service import EvaluationService
from app.services.enactment_service import EnactmentService
from app.schemas.assertion import AssertionCreate
from app.schemas.evaluation import EvaluationCreate
from app.utils.crypto import generate_keypair
from app.workers.ttl_worker import ttl_handler


@pytest.fixture
def db_session():
    """Create a database session for testing."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_data(db_session):
    """Create test agents, schemas, and batches."""
    # Generate keypairs
    producer_private, producer_public = generate_keypair()
    auditor_private, auditor_public = generate_keypair()

    # Create agents
    producer = crud.create_agent(db_session, {
        'id': 'test-producer',
        'name': 'Test Producer',
        'role': RoleType.PRODUCER,
        'public_key': producer_public
    })

    auditor = crud.create_agent(db_session, {
        'id': 'test-auditor',
        'name': 'Test Auditor',
        'role': RoleType.AUDITOR,
        'public_key': auditor_public
    })

    # Create schema
    schema = crud.create_schema(db_session, {
        'id': 'test-schema',
        'name': 'Test Schema',
        'description': 'Test schema for testing',
        'deadline_hours': 1,  # 1 hour for testing
        'required_role': RoleType.AUDITOR
    })

    # Create batch
    batch = crud.create_product_batch(db_session, {
        'batch_id': 'test-batch',
        'product_name': 'Test Product',
        'current_custodian_id': producer.id
    })

    db_session.commit()

    return {
        'producer': producer,
        'auditor': auditor,
        'schema': schema,
        'batch': batch,
        'producer_private': producer_private,
        'auditor_private': auditor_private
    }


def test_assertion_create_and_ttl(db_session, test_data):
    """
    Test: Create assertion with deadline and verify TTL expiry.
    Spec section 11: test_assertion_create_and_ttl
    """
    # Create assertion
    assertion_data = AssertionCreate(
        id='test-assertion-1',
        batch_id=test_data['batch'].batch_id,
        agent_id=test_data['producer'].id,
        schema_id=test_data['schema'].id,
        location_gps='10.0,20.0',
        content_data={'score': 95, 'moisture': '11%'}
    )

    result = AssertionService.create_assertion(db_session, assertion_data)

    # Verify assertion created
    assert result['id'] == 'test-assertion-1'
    assert result['status'] == 'pending'

    # Get assertion from DB
    assertion = crud.get_assertion(db_session, 'test-assertion-1')
    assert assertion is not None
    assert assertion.status == ClaimStatus.PENDING

    # Simulate TTL expiry
    ttl_handler('test-assertion-1')

    # Verify assertion is now timed out
    db_session.expire_all()  # Refresh from DB
    assertion = crud.get_assertion(db_session, 'test-assertion-1')
    assert assertion.status == ClaimStatus.TIMED_OUT


def test_evaluation_verifies_and_enacts(db_session, test_data):
    """
    Test: Create assertion, evaluate it, and verify enactment.
    Spec section 11: test_evaluation_verifies_and_enacts
    """
    # Create assertion
    assertion_data = AssertionCreate(
        id='test-assertion-2',
        batch_id=test_data['batch'].batch_id,
        agent_id=test_data['producer'].id,
        schema_id=test_data['schema'].id,
        location_gps='10.0,20.0',
        content_data={'score': 95, 'moisture': '11%'}
    )

    AssertionService.create_assertion(db_session, assertion_data)

    # Create evaluation (approve)
    evaluation_data = EvaluationCreate(
        id='test-eval-1',
        agent_id=test_data['auditor'].id,
        result=True,
        notes='Looks good'
    )

    result = EvaluationService.create_evaluation(
        db_session,
        'test-assertion-2',
        evaluation_data
    )

    # Verify response includes enactment_id
    assert result['enactment_id'] is not None
    assert result['status'] == 'verified'

    # Verify assertion status is VERIFIED
    db_session.expire_all()
    assertion = crud.get_assertion(db_session, 'test-assertion-2')
    assert assertion.status == ClaimStatus.VERIFIED

    # Verify enactment record exists
    enactment = crud.get_enactment_by_assertion(db_session, 'test-assertion-2')
    assert enactment is not None

    # Simulate enactment worker (pass assertion_id, not enactment.id)
    EnactmentService.enact_assertion(db_session, 'test-assertion-2', actor_id='worker')

    # Verify assertion status is now ENACTED
    db_session.expire_all()
    assertion = crud.get_assertion(db_session, 'test-assertion-2')
    assert assertion.status == ClaimStatus.ENACTED

    # Verify blockchain hash is set
    db_session.expire_all()
    enactment = crud.get_enactment_by_assertion(db_session, 'test-assertion-2')
    assert enactment.blockchain_hash is not None
    assert enactment.blockchain_hash.startswith('0x')


def test_evaluator_cannot_be_asserter(db_session, test_data):
    """
    Test: Evaluator cannot be the same as asserter (C2 constraint).
    Spec section 11: test_evaluator_cannot_be_asserter
    """
    # Create assertion
    assertion_data = AssertionCreate(
        id='test-assertion-3',
        batch_id=test_data['batch'].batch_id,
        agent_id=test_data['producer'].id,
        schema_id=test_data['schema'].id,
        location_gps='10.0,20.0',
        content_data={'score': 95, 'moisture': '11%'}
    )

    AssertionService.create_assertion(db_session, assertion_data)

    # Try to evaluate with same agent (should fail with 409)
    evaluation_data = EvaluationCreate(
        id='test-eval-2',
        agent_id=test_data['producer'].id,  # Same as asserter
        result=True,
        notes='Self-evaluation'
    )

    with pytest.raises(Exception) as exc_info:
        EvaluationService.create_evaluation(
            db_session,
            'test-assertion-3',
            evaluation_data
        )

    # Verify it's a 409 Conflict error
    assert exc_info.value.status_code == 409
    assert 'C2' in str(exc_info.value.detail) or 'same as asserter' in str(exc_info.value.detail)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
