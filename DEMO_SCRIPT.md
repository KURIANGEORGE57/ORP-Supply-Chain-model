# Veritas ORP - Demo Script

## Kerala Coffee Quality Certification Flow

This script demonstrates the complete ORP flow using the Kerala coffee supply chain scenario.

## Prerequisites

- Docker Compose running with all services up
- Database migrations applied
- Seed data loaded

Verify setup:
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}

curl http://localhost:3000
# Should load the UI
```

## Demo Flow

### Part 1: Producer Creates Quality Assertion

**Actor:** Kerala Coffee Producer (agent-001)

**Scenario:** Producer harvests a batch of premium Arabica coffee and claims it meets Grade A quality standards.

**Steps:**

1. Open UI at http://localhost:3000
2. Verify current agent is "Kerala Coffee Producer" (agent-001)
3. Navigate to **"Create Assertion"** tab
4. Fill the form:
   - **Batch ID:** `batch-99` (Kerala Premium Arabica Coffee)
   - **Schema:** `Grade A Quality (24h deadline, requires Auditor)`
   - **Location:** `10.8505,76.2711` (Wayanad, Kerala)
   - **Quality Score:** `95`
   - **Moisture Content:** `11%`
   - **Additional Notes:** "Freshly harvested from high-altitude plantation. Cupping score 88/100."
5. Click **"Create Assertion"**

**Expected Result:**
- Success message with assertion ID
- Backend creates assertion with status `PENDING`
- TTL worker schedules timeout job for 24 hours
- Audit log entry created

**API Call (equivalent):**
```bash
curl -X POST http://localhost:8000/api/v1/assertions \
  -H "Content-Type: application/json" \
  -d '{
    "id": "assertion-demo-001",
    "batch_id": "batch-99",
    "agent_id": "agent-001",
    "schema_id": "grade_a",
    "location_gps": "10.8505,76.2711",
    "content_data": {
      "score": 95,
      "moisture": "11%",
      "notes": "Freshly harvested from high-altitude plantation"
    }
  }'
```

---

### Part 2: Auditor Reviews and Evaluates

**Actor:** Coffee Quality Auditor (agent-002)

**Scenario:** Auditor receives notification of pending assertion, conducts lab tests, and approves the quality claim.

**Steps:**

1. Switch agent using dropdown: **"Switch to Auditor"** (agent-002)
2. Navigate to **"Evaluate Claims"** tab
3. Observe:
   - Pending assertion appears in list
   - Countdown timer shows time remaining (should be ~24 hours)
   - Progress bar shows percentage of deadline remaining
4. Click on the assertion to expand details
5. Review:
   - Batch ID, Agent, Schema
   - GPS location
   - Content data (score, moisture)
6. Add evaluation notes: "Lab tests confirm: moisture 10.8%, no defects detected, cupping score validates producer claim"
7. Click **"Approve"**

**Expected Result:**
- Success message with enactment ID
- Assertion status changes to `VERIFIED`
- Enactment record created
- Worker job enqueued for blockchain anchoring
- Audit log entries created

**API Call (equivalent):**
```bash
curl -X POST http://localhost:8000/api/v1/assertions/assertion-demo-001/evaluations \
  -H "Content-Type: application/json" \
  -d '{
    "id": "eval-demo-001",
    "agent_id": "agent-002",
    "result": true,
    "notes": "Lab tests confirm quality claim"
  }'
```

---

### Part 3: Worker Performs Enactment

**Actor:** System Worker (automatic)

**Scenario:** Worker picks up enactment job from queue and anchors to blockchain.

**Process (automatic):**

1. Worker receives enactment job from Redis queue
2. Computes canonical digest:
   - Fetches assertion data
   - Fetches evaluation data
   - Combines into canonical JSON
   - Computes SHA-256 hash
3. Simulates blockchain anchor (in production, submits to Hyperledger/Ethereum)
4. Updates enactment with transaction hash (e.g., `0xabc123...`)
5. Updates assertion status to `ENACTED`
6. Creates audit log entry

**Monitor Worker:**
```bash
# View worker logs
docker compose logs -f worker

# Should see:
# "Enactment handler triggered for: <enactment-id>"
# "Simulated blockchain anchor: 0x..."
# "Enactment completed: {...}"
```

---

### Part 4: View Complete Timeline

**Actor:** Any stakeholder

**Scenario:** View immutable provenance trail for the coffee batch.

**Steps:**

1. Navigate to **"View Batches"** tab
2. Select **"batch-99 (Kerala Premium Arabica)"**
3. Observe timeline showing:
   - **Assertion Created**
     - Timestamp
     - Agent: agent-001
     - Status: ENACTED
     - Content data with quality metrics
     - Optional: Signature verification badge
   - **Evaluation** (when implemented)
     - Evaluator: agent-002
     - Result: Approved
     - Notes
   - **Enactment**
     - Blockchain hash: `0x...`
     - Timestamp
4. Expand "View Content Data" to see full JSON
5. Note the signature field (if present)

**Expected Result:**
- Complete audit trail from assertion → evaluation → enactment
- All timestamps in chronological order
- Blockchain anchor provides immutable proof
- Can be shared with buyers as quality certificate

---

## Edge Case Demo: Timeout Scenario

### Scenario: Assertion Times Out Without Evaluation

**Purpose:** Demonstrate deadline enforcement and fallback behavior.

**Steps:**

1. Switch to Producer (agent-001)
2. Create new assertion:
   - Batch: `batch-100`
   - Schema: `Logistics Check (12h deadline)`
   - Other fields: fill as desired
3. **DO NOT evaluate** - let it sit
4. Simulate timeout by manually triggering TTL worker:

```bash
# Get assertion ID from UI or API response
ASSERTION_ID="assertion-demo-002"

# Trigger TTL handler manually
docker compose exec backend python -c "
from app.workers.ttl_worker import ttl_handler
ttl_handler('$ASSERTION_ID')
"
```

5. Refresh UI and check assertion status

**Expected Result:**
- Assertion status changes to `TIMED_OUT`
- Audit log records timeout event
- Fallback actions triggered:
  - Batch quality flag may be downgraded
  - Producer notified (in production)
  - Potential penalties applied per business rules

**Check Status:**
```bash
curl http://localhost:8000/api/v1/assertions/$ASSERTION_ID/status
```

Response:
```json
{
  "id": "assertion-demo-002",
  "status": "timed_out",
  "deadline_seconds": 43200,
  "time_elapsed_seconds": 43201,
  "is_near_deadline": false
}
```

---

## Edge Case Demo: C2 Violation (Self-Evaluation)

### Scenario: Producer Attempts to Evaluate Own Assertion

**Purpose:** Demonstrate constraint validation (C2: evaluator ≠ asserter).

**Steps:**

1. Create assertion as Producer (agent-001)
2. Stay as Producer (don't switch agents)
3. Try to evaluate the assertion

**Expected Result:**
- API returns `409 Conflict`
- Error message: "Evaluator cannot be the same as asserter (C2 violation)"
- Assertion status remains `PENDING`

**API Test:**
```bash
# Create assertion
ASSERTION_ID="assertion-demo-003"
curl -X POST http://localhost:8000/api/v1/assertions \
  -H "Content-Type: application/json" \
  -d "{
    \"id\": \"$ASSERTION_ID\",
    \"batch_id\": \"batch-99\",
    \"agent_id\": \"agent-001\",
    \"schema_id\": \"grade_a\",
    \"content_data\": {\"score\": 90}
  }"

# Try to self-evaluate (should fail)
curl -X POST http://localhost:8000/api/v1/assertions/$ASSERTION_ID/evaluations \
  -H "Content-Type: application/json" \
  -d '{
    "id": "eval-demo-003",
    "agent_id": "agent-001",
    "result": true
  }'

# Expected: HTTP 409 Conflict
```

---

## Edge Case Demo: Role Mismatch

### Scenario: Wrong Role Attempts Evaluation

**Purpose:** Demonstrate role-based access control.

**Steps:**

1. Create assertion with schema `grade_a` (requires AUDITOR)
2. Switch to Logistics agent (agent-003)
3. Try to evaluate

**Expected Result:**
- API returns `403 Forbidden`
- Error: "Evaluator role logistics does not match required role auditor"

---

## Production Scenario: Multi-Batch Tracking

### Scenario: Multiple Batches in Transit

**Steps:**

1. Create assertions for both batches:
   - `batch-99` (Premium Arabica) - Grade A certification
   - `batch-100` (Robusta) - Logistics check
2. Switch between agents to evaluate
3. View timeline for each batch separately
4. Demonstrate parallel processing

**Expected Result:**
- System handles multiple assertions concurrently
- Each batch maintains independent timeline
- Deadlines enforced per assertion
- No cross-contamination of data

---

## Monitoring Demo

### View Audit Logs

```bash
# Connect to database
docker compose exec postgres psql -U veritas -d veritas

# Query recent audit logs
SELECT created_at, actor_id, action, payload
FROM audit_log
ORDER BY created_at DESC
LIMIT 10;
```

### Check Redis Queue

```bash
# Connect to Redis
docker compose exec redis redis-cli

# Check queue length
LLEN rq:queue:default

# View scheduled jobs
ZRANGE rq:scheduler:scheduled_jobs 0 -1 WITHSCORES
```

### API Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Get API documentation
open http://localhost:8000/docs
```

---

## Summary

This demo showed:
1. ✅ **Assertion Creation** - Producer claims quality
2. ✅ **Evaluation** - Auditor verifies claim
3. ✅ **Enactment** - Worker anchors to blockchain
4. ✅ **Timeline** - Complete provenance trail
5. ✅ **Timeout Handling** - Deadline enforcement
6. ✅ **Constraint Validation** - C2 (self-evaluation prevention)
7. ✅ **Role-Based Access** - Auditor-only evaluation

**Key Takeaways:**
- Immutable audit trail from source to certification
- Cryptographic signatures ensure authenticity
- Deadline enforcement prevents stale claims
- Role-based permissions ensure proper verification
- Blockchain anchor provides external proof
- All actions logged for compliance

## Next Steps

For production deployment:
1. Configure real blockchain (Hyperledger Fabric or Ethereum L2)
2. Implement actual cryptographic signing in UI
3. Set up email/SMS notifications for timeouts
4. Configure monitoring & alerting (Prometheus + Grafana)
5. Enable TLS/HTTPS
6. Deploy to Kubernetes with HA PostgreSQL/Redis
7. Implement multi-registry federation
8. Add dispute resolution workflow
