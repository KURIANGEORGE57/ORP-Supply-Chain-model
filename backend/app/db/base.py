# backend/app/db/base.py
from .models import Base

# Import all models for Alembic to detect
from .models import Agent, Schema, ProductBatch, Assertion, Evaluation, Enactment, AuditLog

__all__ = ["Base", "Agent", "Schema", "ProductBatch", "Assertion", "Evaluation", "Enactment", "AuditLog"]
