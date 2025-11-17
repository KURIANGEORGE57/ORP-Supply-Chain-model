# Veritas ORP Data Models

## Overview

This document describes the database schema and data models for the ORP Supply Chain system.

## Database Tables

### Agent

Represents actors in the supply chain (producers, auditors, logistics providers, retailers).

| Column | Type | Description |
|--------|------|-------------|
| id | String (PK) | Unique agent identifier |
| name | String | Human-readable name |
| role | Enum (RoleType) | Agent's role (PRODUCER, AUDITOR, LOGISTICS, RETAILER) |
| public_key | String | RSA public key for signature verification |
| created_at | DateTime | Creation timestamp |

### Schema

Defines assertion schemas with validation rules and deadlines.

| Column | Type | Description |
|--------|------|-------------|
| id | String (PK) | Unique schema identifier |
| name | String | Schema name |
| description | Text | Schema description |
| deadline_hours | Integer | Deadline in hours (Δ) |
| required_role | Enum (RoleType) | Required evaluator role |
| created_at | DateTime | Creation timestamp |

### ProductBatch

Represents a batch of products moving through the supply chain.

| Column | Type | Description |
|--------|------|-------------|
| batch_id | String (PK) | Unique batch identifier |
| product_name | String | Product name/description |
| current_custodian_id | String (FK→Agent) | Current custodian |
| created_at | DateTime | Creation timestamp |

### Assertion

Claims made by agents about product batches.

| Column | Type | Description |
|--------|------|-------------|
| id | String (PK) | Unique assertion identifier |
| batch_id | String (FK→ProductBatch) | Associated batch |
| agent_id | String (FK→Agent) | Asserting agent |
| schema_id | String (FK→Schema) | Schema defining this assertion |
| timestamp | DateTime | Assertion creation time |
| location_gps | String | GPS coordinates (optional) |
| content_data | JSON | Assertion content (score, moisture, etc.) |
| status | Enum (ClaimStatus) | Current status |
| signature | String | Cryptographic signature (optional) |

**Indexes:**
- `(batch_id, status, timestamp)` - Fast queries for batch history

**Status Values:**
- PENDING - Awaiting evaluation
- VERIFIED - Approved
- REJECTED - Denied
- TIMED_OUT - Deadline expired
- ENACTED - Blockchain anchored

### Evaluation

Evaluations of assertions by authorized agents.

| Column | Type | Description |
|--------|------|-------------|
| id | String (PK) | Unique evaluation identifier |
| assertion_id | String (FK→Assertion) | Assertion being evaluated |
| agent_id | String (FK→Agent) | Evaluating agent |
| timestamp | DateTime | Evaluation timestamp |
| result | Boolean | Approve (true) or reject (false) |
| notes | Text | Evaluation notes |
| signature | String | Cryptographic signature (optional) |

### Enactment

Records of blockchain anchoring for verified assertions.

| Column | Type | Description |
|--------|------|-------------|
| id | String (PK) | Unique enactment identifier |
| assertion_id | String (FK→Assertion) | Associated assertion |
| timestamp | DateTime | Enactment timestamp |
| blockchain_hash | String | Transaction hash on blockchain |
| enacted_by | String (FK→Agent) | Actor performing enactment |
| metadata | JSON | Additional metadata |

### AuditLog

Immutable audit trail of all system actions.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK, Auto) | Sequential log ID |
| created_at | DateTime | Log entry timestamp |
| actor_id | String | Agent performing action |
| action | String | Action type (assertion_created, etc.) |
| payload | JSON | Action details |

## Enums

### RoleType
```python
class RoleType(enum.Enum):
    PRODUCER = "producer"
    AUDITOR = "auditor"
    LOGISTICS = "logistics"
    RETAILER = "retailer"
```

### ClaimStatus
```python
class ClaimStatus(enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    TIMED_OUT = "timed_out"
    ENACTED = "enacted"
```

## Relationships

```
Agent ─┬─> Assertion (agent_id)
       ├─> Evaluation (agent_id)
       └─> ProductBatch (current_custodian_id)

Schema ──> Assertion (schema_id)

ProductBatch ──> Assertion (batch_id)

Assertion ─┬─> Evaluation (assertion_id)
           └─> Enactment (assertion_id)
```

## Business Logic Constraints

### C1: Schema-Role Match
Evaluator's role MUST match schema's `required_role`.

### C2: Self-Evaluation Prevention
Evaluator MUST NOT be the same agent as asserter (`evaluation.agent_id ≠ assertion.agent_id`).

### C3: Deadline Enforcement
Evaluation MUST occur within `schema.deadline_hours` from assertion timestamp.

### C4: Status Transitions
Valid status transitions:
- PENDING → VERIFIED (on approval)
- PENDING → REJECTED (on rejection)
- PENDING → TIMED_OUT (on deadline expiry)
- VERIFIED → ENACTED (after blockchain anchor)

## Canonical Digest Computation

Enactment digest combines:
1. Assertion data (canonical JSON)
2. Evaluation data (canonical JSON)
3. Metadata (canonical JSON)

SHA-256 hash of canonical representation.

Example:
```python
digest = sha256(canonical_json({
    'assertion': {...},
    'evaluation': {...},
    'metadata': {...}
}))
```

## Indexing Strategy

### High-Priority Indexes
1. `assertions(batch_id, status, timestamp)` - Batch timeline queries
2. `assertions(status)` - Pending assertions list
3. `evaluations(assertion_id)` - Lookup evaluation for assertion
4. `enactments(assertion_id)` - Lookup enactment for assertion
5. `audit_log(created_at)` - Chronological audit queries

### Future Indexes (Performance Optimization)
- `assertions(agent_id, timestamp)` - Agent activity history
- `assertions(schema_id, status)` - Schema-specific analytics
- `audit_log(actor_id, action, created_at)` - Actor audit trail
