#!/usr/bin/env python3
"""
Seed script for ORP Supply Chain MVP.
Creates test agents, schemas, and product batches.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import get_db_session
from app.db import crud
from app.db.models import RoleType
from app.utils.crypto import generate_keypair
from app.utils.logging import logger

def seed_database():
    """Seed database with initial test data."""
    logger.info("Starting database seeding...")

    with get_db_session() as session:
        # Generate keypairs for test agents
        producer_private, producer_public = generate_keypair()
        auditor_private, auditor_public = generate_keypair()
        logistics_private, logistics_public = generate_keypair()

        # Create Agents
        logger.info("Creating agents...")

        agent_001 = crud.create_agent(session, {
            'id': 'agent-001',
            'name': 'Kerala Coffee Producer',
            'role': RoleType.PRODUCER,
            'public_key': producer_public
        })
        logger.info(f"Created agent: {agent_001.id} ({agent_001.name})")

        agent_002 = crud.create_agent(session, {
            'id': 'agent-002',
            'name': 'Coffee Quality Auditor',
            'role': RoleType.AUDITOR,
            'public_key': auditor_public
        })
        logger.info(f"Created agent: {agent_002.id} ({agent_002.name})")

        agent_003 = crud.create_agent(session, {
            'id': 'agent-003',
            'name': 'Logistics Provider',
            'role': RoleType.LOGISTICS,
            'public_key': logistics_public
        })
        logger.info(f"Created agent: {agent_003.id} ({agent_003.name})")

        # Create Schemas
        logger.info("Creating schemas...")

        schema_grade_a = crud.create_schema(session, {
            'id': 'grade_a',
            'name': 'Grade A Quality Certification',
            'description': 'Premium coffee quality certification requiring auditor verification',
            'deadline_hours': 24,
            'required_role': RoleType.AUDITOR
        })
        logger.info(f"Created schema: {schema_grade_a.id} (deadline: {schema_grade_a.deadline_hours}h)")

        schema_logistics = crud.create_schema(session, {
            'id': 'logistics_check',
            'name': 'Logistics Quality Check',
            'description': 'Verification of proper storage and transport conditions',
            'deadline_hours': 12,
            'required_role': RoleType.LOGISTICS
        })
        logger.info(f"Created schema: {schema_logistics.id} (deadline: {schema_logistics.deadline_hours}h)")

        # Create Product Batches
        logger.info("Creating product batches...")

        batch_99 = crud.create_product_batch(session, {
            'batch_id': 'batch-99',
            'product_name': 'Kerala Premium Arabica Coffee',
            'current_custodian_id': 'agent-001'
        })
        logger.info(f"Created batch: {batch_99.batch_id} ({batch_99.product_name})")

        batch_100 = crud.create_product_batch(session, {
            'batch_id': 'batch-100',
            'product_name': 'Kerala Robusta Coffee',
            'current_custodian_id': 'agent-001'
        })
        logger.info(f"Created batch: {batch_100.batch_id} ({batch_100.product_name})")

        session.commit()

        # Save private keys to file for demo/testing
        keys_dir = os.path.join(os.path.dirname(__file__), 'test_keys')
        os.makedirs(keys_dir, exist_ok=True)

        with open(os.path.join(keys_dir, 'producer_private.pem'), 'w') as f:
            f.write(producer_private)

        with open(os.path.join(keys_dir, 'auditor_private.pem'), 'w') as f:
            f.write(auditor_private)

        with open(os.path.join(keys_dir, 'logistics_private.pem'), 'w') as f:
            f.write(logistics_private)

        logger.info(f"Saved test private keys to {keys_dir}")

        logger.info("Database seeding completed successfully!")

        print("\n" + "="*60)
        print("SEED DATA SUMMARY")
        print("="*60)
        print("\nAgents:")
        print(f"  - {agent_001.id}: {agent_001.name} ({agent_001.role.value})")
        print(f"  - {agent_002.id}: {agent_002.name} ({agent_002.role.value})")
        print(f"  - {agent_003.id}: {agent_003.name} ({agent_003.role.value})")
        print("\nSchemas:")
        print(f"  - {schema_grade_a.id}: {schema_grade_a.name} ({schema_grade_a.deadline_hours}h deadline)")
        print(f"  - {schema_logistics.id}: {schema_logistics.name} ({schema_logistics.deadline_hours}h deadline)")
        print("\nBatches:")
        print(f"  - {batch_99.batch_id}: {batch_99.product_name}")
        print(f"  - {batch_100.batch_id}: {batch_100.product_name}")
        print("\n" + "="*60)

if __name__ == "__main__":
    seed_database()
