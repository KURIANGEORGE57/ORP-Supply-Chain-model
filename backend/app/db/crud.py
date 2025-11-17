# backend/app/db/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import select
from .models import Agent, Schema, ProductBatch, Assertion, Evaluation, Enactment, AuditLog, ClaimStatus
from typing import Optional, List
from datetime import datetime

# Agent operations
def get_agent(db: Session, agent_id: str) -> Optional[Agent]:
    """Get agent by ID."""
    return db.query(Agent).filter(Agent.id == agent_id).first()

def create_agent(db: Session, agent_data: dict) -> Agent:
    """Create new agent."""
    agent = Agent(**agent_data)
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent

# Schema operations
def get_schema(db: Session, schema_id: str) -> Optional[Schema]:
    """Get schema by ID."""
    return db.query(Schema).filter(Schema.id == schema_id).first()

def create_schema(db: Session, schema_data: dict) -> Schema:
    """Create new schema."""
    schema = Schema(**schema_data)
    db.add(schema)
    db.commit()
    db.refresh(schema)
    return schema

# ProductBatch operations
def get_product_batch(db: Session, batch_id: str) -> Optional[ProductBatch]:
    """Get product batch by ID."""
    return db.query(ProductBatch).filter(ProductBatch.batch_id == batch_id).first()

def create_product_batch(db: Session, batch_data: dict) -> ProductBatch:
    """Create new product batch."""
    batch = ProductBatch(**batch_data)
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch

# Assertion operations
def get_assertion(db: Session, assertion_id: str) -> Optional[Assertion]:
    """Get assertion by ID."""
    return db.query(Assertion).filter(Assertion.id == assertion_id).first()

def get_assertion_for_update(db: Session, assertion_id: str) -> Optional[Assertion]:
    """Get assertion with row lock for update."""
    return db.query(Assertion).filter(Assertion.id == assertion_id).with_for_update().first()

def get_assertions_by_status(db: Session, status: ClaimStatus, limit: int = 100) -> List[Assertion]:
    """Get assertions by status."""
    return db.query(Assertion).filter(Assertion.status == status).limit(limit).all()

def get_assertions_by_batch(db: Session, batch_id: str) -> List[Assertion]:
    """Get all assertions for a batch."""
    return db.query(Assertion).filter(Assertion.batch_id == batch_id).order_by(Assertion.timestamp.desc()).all()

def create_assertion(db: Session, assertion_data: dict) -> Assertion:
    """Create new assertion."""
    assertion = Assertion(**assertion_data)
    db.add(assertion)
    db.commit()
    db.refresh(assertion)
    return assertion

def update_assertion_status(db: Session, assertion_id: str, status: ClaimStatus) -> Optional[Assertion]:
    """Update assertion status."""
    assertion = get_assertion_for_update(db, assertion_id)
    if assertion:
        assertion.status = status
        db.commit()
        db.refresh(assertion)
    return assertion

def mark_assertion_timed_out(db: Session, assertion_id: str) -> Optional[Assertion]:
    """Mark assertion as timed out."""
    return update_assertion_status(db, assertion_id, ClaimStatus.TIMED_OUT)

# Evaluation operations
def get_evaluation_by_assertion(db: Session, assertion_id: str) -> Optional[Evaluation]:
    """Get evaluation for an assertion."""
    return db.query(Evaluation).filter(Evaluation.assertion_id == assertion_id).first()

def create_evaluation(db: Session, evaluation_data: dict) -> Evaluation:
    """Create new evaluation."""
    evaluation = Evaluation(**evaluation_data)
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return evaluation

# Enactment operations
def get_enactment_by_assertion(db: Session, assertion_id: str) -> Optional[Enactment]:
    """Get enactment for an assertion."""
    return db.query(Enactment).filter(Enactment.assertion_id == assertion_id).first()

def create_enactment(db: Session, enactment_data: dict) -> Enactment:
    """Create new enactment."""
    enactment = Enactment(**enactment_data)
    db.add(enactment)
    db.commit()
    db.refresh(enactment)
    return enactment

def update_enactment_hash(db: Session, enactment_id: str, blockchain_hash: str) -> Optional[Enactment]:
    """Update enactment with blockchain hash."""
    enactment = db.query(Enactment).filter(Enactment.id == enactment_id).first()
    if enactment:
        enactment.blockchain_hash = blockchain_hash
        db.commit()
        db.refresh(enactment)
    return enactment

# AuditLog operations
def create_audit_log(db: Session, actor_id: str, action: str, payload: dict) -> AuditLog:
    """Create audit log entry."""
    log_entry = AuditLog(
        actor_id=actor_id,
        action=action,
        payload=payload,
        created_at=datetime.utcnow()
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry
