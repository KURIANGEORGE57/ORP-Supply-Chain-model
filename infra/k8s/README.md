# Kubernetes Deployment

## Prerequisites

- Kubernetes cluster (GKE, EKS, AKS, or local minikube)
- kubectl configured
- Docker images built and pushed to registry
- Managed PostgreSQL and Redis (recommended) or deploy StatefulSets

## Deployment Steps

### 1. Create Namespace
```bash
kubectl create namespace veritas
kubectl config set-context --current --namespace=veritas
```

### 2. Create Secrets
```bash
kubectl create secret generic veritas-secrets \
  --from-literal=database-url='postgresql://user:pass@postgres-host:5432/veritas' \
  --from-literal=redis-url='redis://redis-host:6379/0' \
  --from-literal=secret-key='your-secret-key-32-chars' \
  --from-literal=service-token='your-service-token'
```

Or use external secret management (Vault, AWS Secrets Manager):
```bash
# Install external-secrets operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets-system --create-namespace

# Create SecretStore and ExternalSecret (examples in docs)
```

### 3. Deploy Backend
```bash
kubectl apply -f backend-deployment.yaml
```

Verify:
```bash
kubectl get pods -l app=veritas-backend
kubectl logs -f deployment/veritas-backend
```

### 4. Deploy Worker
```bash
kubectl apply -f worker-deployment.yaml
```

Verify:
```bash
kubectl get pods -l app=veritas-worker
kubectl logs -f deployment/veritas-worker
```

### 5. Deploy UI
```bash
kubectl apply -f ui-deployment.yaml
```

Verify:
```bash
kubectl get pods -l app=veritas-ui
```

### 6. Run Migrations
```bash
# Get backend pod name
BACKEND_POD=$(kubectl get pods -l app=veritas-backend -o jsonpath='{.items[0].metadata.name}')

# Run migrations
kubectl exec -it $BACKEND_POD -- alembic upgrade head
```

### 7. Seed Data
```bash
kubectl exec -it $BACKEND_POD -- python scripts/seed.py
```

### 8. Access Application
```bash
# Get external IPs
kubectl get services

# Backend API
BACKEND_IP=$(kubectl get svc veritas-backend -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "API: http://$BACKEND_IP/docs"

# UI
UI_IP=$(kubectl get svc veritas-ui -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "UI: http://$UI_IP"
```

## Production Recommendations

### Use Managed Services
- **PostgreSQL:** AWS RDS, Google Cloud SQL, Azure Database
- **Redis:** AWS ElastiCache, Google Cloud Memorystore, Azure Cache

Benefits:
- Automated backups
- High availability
- Automatic failover
- Monitoring & alerts

### TLS/Ingress
Create Ingress with TLS:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: veritas-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.veritas.example.com
    - ui.veritas.example.com
    secretName: veritas-tls
  rules:
  - host: api.veritas.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: veritas-backend
            port:
              number: 80
  - host: ui.veritas.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: veritas-ui
            port:
              number: 80
```

### Monitoring
Deploy Prometheus & Grafana:
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack

# Import Grafana dashboards for FastAPI metrics
```

### Autoscaling
HPA is already configured for workers. Add for backend:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: veritas-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: veritas-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Resource Quotas
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: veritas-quota
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
```

## Troubleshooting

### Pod not starting
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Database connection issues
```bash
# Test from backend pod
kubectl exec -it $BACKEND_POD -- bash
psql $DATABASE_URL -c "SELECT 1"
```

### Redis connection issues
```bash
kubectl exec -it $BACKEND_POD -- bash
redis-cli -u $REDIS_URL ping
```

### Migration failures
```bash
# Check current revision
kubectl exec -it $BACKEND_POD -- alembic current

# Downgrade if needed
kubectl exec -it $BACKEND_POD -- alembic downgrade -1

# Re-run upgrade
kubectl exec -it $BACKEND_POD -- alembic upgrade head
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Deploy to Kubernetes

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2

    - name: Build & Push Docker images
      run: |
        docker build -t gcr.io/project/veritas-backend:${{ github.sha }} ./backend
        docker push gcr.io/project/veritas-backend:${{ github.sha }}

    - name: Deploy to GKE
      run: |
        kubectl set image deployment/veritas-backend backend=gcr.io/project/veritas-backend:${{ github.sha }}
        kubectl rollout status deployment/veritas-backend
```

## Cleanup
```bash
kubectl delete -f .
kubectl delete namespace veritas
```
