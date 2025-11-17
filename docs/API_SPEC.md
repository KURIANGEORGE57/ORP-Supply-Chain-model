# Veritas ORP API Specification

## Overview

This document defines the exact API contract for the Veritas Open Registry Protocol (ORP) backend.

Base URL: `http://localhost:8000/api/v1`

## Authentication

JWT Bearer tokens are used for authentication. Include in request headers:
```
Authorization: Bearer <token>
```

Worker endpoints require service token in header:
```
X-Service-Token: <service-token>
```

## Endpoints

### 1. Create Assertion

**POST** `/assertions`

Create a new assertion with signature validation and TTL scheduling.

**Request Body:**
```json
{
  "id": "uuid-assert-0001",
  "batch_id": "batch-99",
  "agent_id": "agent-001",
  "schema_id": "grade_a",
  "timestamp": "2025-11-17T10:00:00Z",
  "location_gps": "10.8505,76.2711",
  "content_data": {"score": 95, "moisture": "11%"},
  "signature": "hex-or-base64-signature"
}
```

**Response (201 Created):**
```json
{
  "id": "uuid-assert-0001",
  "status": "pending",
  "message": "Assertion created; deadline scheduled"
}
```

**Error Codes:**
- `400` - Invalid payload or schema/batch not found
- `401` - Invalid signature

---

### 2. Create Evaluation

**POST** `/assertions/{assertion_id}/evaluations`

Create an evaluation for an existing assertion.

**Path Parameters:**
- `assertion_id` - ID of the assertion to evaluate

**Request Body:**
```json
{
  "id": "uuid-eval-0001",
  "agent_id": "agent-002",
  "timestamp": "2025-11-17T14:00:00Z",
  "result": true,
  "notes": "lab OK",
  "signature": "..."
}
```

**Response (200 OK):**
```json
{
  "id": "uuid-eval-0001",
  "assertion_id": "uuid-assert-0001",
  "status": "verified",
  "enactment_id": "uuid-enact-0001"
}
```

**Error Codes:**
- `400` - Invalid request
- `401` - Invalid signature
- `403` - Evaluator role does not match required role
- `404` - Assertion not found
- `409` - Evaluator is same as asserter (C2 violation)
- `410` - Assertion has timed out

---

### 3. Get Assertion Status

**GET** `/assertions/{assertion_id}/status`

Get current status and deadline information for an assertion.

**Response (200 OK):**
```json
{
  "id": "uuid-assert-0001",
  "status": "pending",
  "deadline_seconds": 86400,
  "time_elapsed_seconds": 14400,
  "is_near_deadline": false
}
```

---

### 4. Get Assertions (List)

**GET** `/assertions`

Get list of assertions filtered by status.

**Query Parameters:**
- `status` - Filter by status (pending, verified, rejected, timed_out, enacted)
- `limit` - Max results (default 100)

**Response (200 OK):**
```json
[
  {
    "id": "uuid-assert-0001",
    "batch_id": "batch-99",
    "agent_id": "agent-001",
    "schema_id": "grade_a",
    "timestamp": "2025-11-17T10:00:00Z",
    "location_gps": "10.8505,76.2711",
    "content_data": {"score": 95, "moisture": "11%"},
    "status": "pending"
  }
]
```

---

### 5. Enact Assertion (Worker Only)

**POST** `/assertions/{assertion_id}/enact`

Perform enactment (compute digest and anchor to blockchain).

**Protected:** Requires service token in `X-Service-Token` header.

**Request Body:**
```json
{
  "actor_id": "worker"
}
```

**Response (200 OK):**
```json
{
  "enactment_id": "uuid-enact-0001",
  "blockchain_hash": "0xabc123...",
  "timestamp": "2025-11-17T14:05:00Z"
}
```

---

## Status Values

Assertions progress through the following statuses:

- `pending` - Awaiting evaluation
- `verified` - Approved by evaluator
- `rejected` - Rejected by evaluator
- `timed_out` - Deadline expired without evaluation
- `enacted` - Anchored to blockchain

## Business Rules

### C2 Constraint
Evaluator MUST NOT be the same agent as the asserter. Violation returns `409 Conflict`.

### Deadline Enforcement
Assertions have a deadline based on schema `deadline_hours`. If evaluation occurs after deadline, assertion is marked `timed_out` and evaluation fails with `410 Gone`.

### Role Matching
Evaluator's role MUST match schema's `required_role`. Mismatch returns `403 Forbidden`.

### Signature Verification
If `signature` is provided, it MUST be valid according to agent's public key. Invalid signature returns `401 Unauthorized`.

## Canonicalization

All signed payloads use deterministic JSON canonicalization (RFC 8785 inspired):
- Sorted keys
- No whitespace
- Consistent encoding

Example canonical assertion:
```json
{"agent_id":"agent-001","batch_id":"batch-99","content_data":{"moisture":"11%","score":95},"id":"uuid-assert-0001","location_gps":"10.8505,76.2711","schema_id":"grade_a","timestamp":"2025-11-17T10:00:00Z"}
```
