# Veritas ORP - Supply Chain MVP

## Executive Summary

A FastAPI + PostgreSQL backend implementing ORP models with **Assertions**, **Evaluations**, and **Enactments**. Includes a Redis-backed worker that enforces deadline (Δ) TTL and performs enactments with timeouts, plus a React UI demo showing Kerala coffee flow.

**Stack:** FastAPI, PostgreSQL, Redis, RQ (worker queue), React + Vite

**Demo Use Case:** Kerala coffee supply chain with quality certification

## Architecture

```
┌─────────────────┐
│   React UI      │  Port 3000
│  (Vite + React) │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│  FastAPI        │  Port 8000
│  Backend        │
└────┬────────────┘
     │
     ├──> PostgreSQL (Port 5432)
     │    - Assertions, Evaluations, Enactments
     │    - Agents, Schemas, ProductBatches
     │
     └──> Redis (Port 6379)
          - Job Queue (RQ)
          - TTL Scheduling

Workers:
- TTL Worker: Monitors deadlines, marks timeouts
- Enactment Worker: Computes digests, anchors to blockchain
```

## Quick Start (Docker Compose)

### Prerequisites
- Docker & Docker Compose
- Git

### 1. Clone & Navigate
```bash
git clone <repository-url>
cd ORP-Supply-Chain-model
```

### 2. Build & Start Services
```bash
cd infra
docker compose up --build -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- Backend API (port 8000)
- Worker (background)
- UI (port 3000)

### 3. Run Migrations
```bash
docker compose exec backend bash -c "alembic upgrade head"
```

### 4. Seed Test Data
```bash
docker compose exec backend python scripts/seed.py
```

This creates:
- 3 agents (producer, auditor, logistics)
- 2 schemas (grade_a, logistics_check)
- 2 product batches (Kerala coffee)

### 5. Open Application
- **UI:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **API:** http://localhost:8000/api/v1

## Demo Script (Kerala Coffee Flow)

### Scenario: Premium Coffee Quality Certification

**Actors:**
- `agent-001` - Kerala Coffee Producer
- `agent-002` - Coffee Quality Auditor
- `batch-99` - Kerala Premium Arabica Coffee

**Flow:**

1. **Producer Creates Assertion**
   - Navigate to UI → "Create Assertion"
   - Switch agent to "Kerala Coffee Producer"
   - Fill form:
     - Batch: `batch-99`
     - Schema: `Grade A Quality (24h deadline)`
     - Score: `95`
     - Moisture: `11%`
   - Submit → Assertion created (status: PENDING)
   - TTL scheduled for 24 hours

2. **Auditor Evaluates**
   - Switch agent to "Coffee Quality Auditor"
   - Navigate to "Evaluate Claims"
   - See pending assertion with countdown timer
   - Click assertion → Review data
   - Add notes: "Lab tests confirm premium quality"
   - Click "Approve"
   - → Evaluation created, Assertion status: VERIFIED
   - → Enactment queued

3. **Worker Enacts**
   - Worker automatically:
     - Computes canonical digest (SHA-256)
     - Simulates blockchain anchor (tx hash: 0x...)
     - Updates Assertion status: ENACTED

4. **View Timeline**
   - Navigate to "View Batches"
   - Select `batch-99`
   - See complete timeline:
     - Assertion (with signature)
     - Evaluation (with approval)
     - Enactment (with blockchain hash)

### Edge Case: Timeout Demo

1. Create assertion with 12h deadline (Logistics schema)
2. Do NOT evaluate
3. Simulate TTL expiry:
   ```bash
   docker compose exec backend python -c "from app.workers.ttl_worker import ttl_handler; ttl_handler('assertion-id')"
   ```
4. Assertion status → TIMED_OUT
5. System applies fallback (quality downgrade, notifications)

## Project Structure

```
ORP-Supply-Chain-model/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   ├── core/            # Config, security
│   │   ├── db/              # Models, CRUD, session
│   │   ├── services/        # Business logic
│   │   ├── workers/         # TTL & enactment workers
│   │   ├── schemas/         # Pydantic DTOs
│   │   └── utils/           # Canonicalize, crypto, logging
│   ├── alembic/             # Database migrations
│   ├── scripts/             # Seed data, utilities
│   ├── requirements.txt
│   └── Dockerfile
├── ui/
│   ├── src/
│   │   ├── pages/           # AssertionForm, EvaluationPanel, BatchView
│   │   └── components/      # Timeline, Countdown
│   ├── package.json
│   └── Dockerfile
├── infra/
│   ├── docker-compose.yml   # Local dev setup
│   └── k8s/                 # Kubernetes manifests (production)
├── tests/
│   └── backend/             # Pytest tests
└── docs/
    ├── API_SPEC.md          # API contract
    └── DATA_MODELS.md       # Database schema
```

## API Endpoints

See [docs/API_SPEC.md](docs/API_SPEC.md) for complete API documentation.

**Key Endpoints:**
- `POST /api/v1/assertions` - Create assertion
- `POST /api/v1/assertions/{id}/evaluations` - Evaluate assertion
- `GET /api/v1/assertions/{id}/status` - Get status & countdown
- `GET /api/v1/assertions?status=pending` - List pending assertions

## Business Rules

### C1: Role Matching
Evaluator's role MUST match schema's `required_role`. Violation → `403 Forbidden`.

### C2: Self-Evaluation Prevention
Evaluator CANNOT be the same agent as asserter. Violation → `409 Conflict`.

### C3: Deadline Enforcement (Δ)
Evaluation MUST occur within `deadline_hours` from assertion timestamp. Late evaluation → `410 Gone`, assertion marked `TIMED_OUT`.

### Signature Verification
If `signature` provided, it MUST verify against agent's `public_key` using RSA-PSS-SHA256. Invalid → `401 Unauthorized`.

### Canonical Digest
Enactments compute SHA-256 digest of canonical JSON (RFC 8785 inspired):
- Sorted keys
- No whitespace
- Deterministic encoding

## Testing

### Run Unit Tests
```bash
cd tests/backend
pytest test_assertion_flow.py -v
```

**Test Cases:**
1. `test_assertion_create_and_ttl` - Verify TTL scheduling and timeout
2. `test_evaluation_verifies_and_enacts` - Full flow: assertion → evaluation → enactment
3. `test_evaluator_cannot_be_asserter` - C2 constraint validation

### Integration Tests (Future)
- Use testcontainers for PostgreSQL
- Test end-to-end flows with real DB
- Verify worker job execution

## Development

### Backend Development
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run locally (requires PostgreSQL & Redis)
export DATABASE_URL="postgresql://veritas:veritas_pass@localhost:5432/veritas"
export REDIS_URL="redis://localhost:6379/0"
uvicorn app.main:app --reload

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### UI Development
```bash
cd ui

# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build
```

### Worker Development
```bash
cd backend

# Run worker locally
python -m rq worker default
```

## Production Deployment

### Kubernetes (k8s)

See `infra/k8s/` for manifests.

**Components:**
- Deployment: backend (3 replicas)
- Deployment: worker (2 replicas)
- Deployment: ui (2 replicas)
- StatefulSet: PostgreSQL (managed DB recommended)
- StatefulSet: Redis (managed cache recommended)
- Service: backend (LoadBalancer)
- Service: ui (LoadBalancer)
- Ingress: TLS termination

**Secrets Management:**
- Use Kubernetes Secrets or external vault (HashiCorp Vault, AWS Secrets Manager)
- Mount service tokens, DB credentials

**Scaling:**
- HPA for backend & worker based on CPU/memory
- Monitor queue depth for worker scaling

### Security Checklist

- [x] TLS for all ingress (nginx/HAProxy)
- [x] JWT authentication for API
- [x] Service tokens for worker-backend communication
- [x] Signature verification (RSA-PSS-SHA256)
- [x] Rate limiting on POST endpoints
- [x] Input validation & sanitization
- [ ] Encrypt PII fields at rest (future)
- [ ] Key rotation policy (future)

## Observability

### Metrics (Prometheus)
- `veritas_assertions_total{schema}`
- `veritas_assertions_timed_out_total{schema}`
- `veritas_evaluations_total{schema}`
- `veritas_enactments_total{schema}`
- `veritas_deadline_latency_seconds` (histogram)

### Alerts (Grafana)
- **HighTimedOutRate:** >5% assertions timing out in 1h window
- **WorkerBacklog:** Queue depth >100 for >5min
- **DatabaseConnections:** Pool exhaustion

### Logging
- Structured JSON logs
- Log levels: INFO (default), DEBUG (dev), ERROR (always)
- Audit log table for compliance

## Future Extensions

1. **Blockchain Anchor (Production)**
   - Integrate Hyperledger Fabric (permissioned) or Ethereum L2
   - Merkle batching for gas savings
   - Verify on-chain anchors

2. **Multi-Signer Assertions**
   - Support multi-party co-signing
   - Threshold signatures (m-of-n)

3. **Schema Editor UI**
   - Visual schema designer
   - Bridge rule DSL (safe subset of JS or JSON-rules)

4. **Federation**
   - Multiple Γ registries
   - Schema equivalence negotiation
   - Cross-registry assertions

5. **Role Delegation**
   - Temporary role assignment
   - Revocation workflows
   - Delegation chains

6. **Dispute Resolution**
   - Arbitration module
   - Multi-stage appeals
   - Evidence attachments

## License

MIT License (or specify your license)

## Support

- **Issues:** [GitHub Issues](https://github.com/your-repo/issues)
- **Docs:** [Documentation](./docs/)
- **API Reference:** [API_SPEC.md](./docs/API_SPEC.md)

## Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## Acknowledgments

- Open Registry Protocol (ORP) specification
- Kerala coffee supply chain use case
- FastAPI, SQLAlchemy, React communities
