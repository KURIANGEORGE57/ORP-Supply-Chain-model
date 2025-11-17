# backend/app/db/models.py
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import Column, String, Integer, DateTime, Enum as SAEnum, JSON, ForeignKey, Text, Boolean
import enum
from datetime import datetime

Base = declarative_base()

class RoleType(enum.Enum):
    PRODUCER = "producer"
    AUDITOR = "auditor"
    LOGISTICS = "logistics"
    RETAILER = "retailer"

class ClaimStatus(enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    TIMED_OUT = "timed_out"
    ENACTED = "enacted"

class Agent(Base):
    __tablename__ = 'agents'
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    role = Column(SAEnum(RoleType), nullable=False)
    public_key = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Schema(Base):
    __tablename__ = 'schemas'
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    deadline_hours = Column(Integer, nullable=False)
    required_role = Column(SAEnum(RoleType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProductBatch(Base):
    __tablename__ = 'product_batches'
    batch_id = Column(String, primary_key=True)
    product_name = Column(String, nullable=False)
    current_custodian_id = Column(String, ForeignKey('agents.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    custodian = relationship('Agent', foreign_keys=[current_custodian_id])

class Assertion(Base):
    __tablename__ = 'assertions'
    id = Column(String, primary_key=True)
    batch_id = Column(String, ForeignKey('product_batches.batch_id'), nullable=False)
    agent_id = Column(String, ForeignKey('agents.id'), nullable=False)
    schema_id = Column(String, ForeignKey('schemas.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    location_gps = Column(String)
    content_data = Column(JSON)
    status = Column(SAEnum(ClaimStatus), default=ClaimStatus.PENDING)
    signature = Column(String, nullable=True)

    batch = relationship('ProductBatch')
    agent = relationship('Agent')
    schema = relationship('Schema')

class Evaluation(Base):
    __tablename__ = 'evaluations'
    id = Column(String, primary_key=True)
    assertion_id = Column(String, ForeignKey('assertions.id'), nullable=False)
    agent_id = Column(String, ForeignKey('agents.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    result = Column(Boolean, nullable=False)
    notes = Column(Text)
    signature = Column(String, nullable=True)

    assertion = relationship('Assertion')
    agent = relationship('Agent')

class Enactment(Base):
    __tablename__ = 'enactments'
    id = Column(String, primary_key=True)
    assertion_id = Column(String, ForeignKey('assertions.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    blockchain_hash = Column(String, nullable=True)
    enacted_by = Column(String, ForeignKey('agents.id'), nullable=True)
    metadata = Column(JSON, nullable=True)

    assertion = relationship('Assertion')
    actor = relationship('Agent', foreign_keys=[enacted_by])

class AuditLog(Base):
    __tablename__ = 'audit_log'
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    actor_id = Column(String)
    action = Column(String)
    payload = Column(JSON)
