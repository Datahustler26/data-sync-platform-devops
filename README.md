# 🚀 BrightEdge Platform — `data-sync` Microservice Integration

[![Kubernetes](https://img.shields.io/badge/Kubernetes-v1.28+-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![Helm](https://img.shields.io/badge/Helm-v3-0F1689?style=for-the-badge&logo=helm&logoColor=white)](https://helm.sh/)
[![Ansible](https://img.shields.io/badge/Ansible-2.10+-EE0000?style=for-the-badge&logo=ansible&logoColor=white)](https://www.ansible.com/)
[![GCP GKE](https://img.shields.io/badge/GCP-GKE-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)](https://cloud.google.com/kubernetes-engine)
[![Python FastAPI](https://img.shields.io/badge/FastAPI-Python_3.9-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Prometheus](https://img.shields.io/badge/Prometheus-Monitoring-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)](https://prometheus.io/)

Production-grade DevOps deployment platform for BrightEdge's **`data-sync`** high-throughput Python FastAPI microservice. Manages containerized GKE workloads via Helm & Kustomize and VM-based workloads via Ansible roles and playbooks.

---

## 🏗️ End-to-End Platform Architecture

The diagram below illustrates how the **`data-sync`** microservice operates across both **GKE Kubernetes Clusters** and **Ansible-Managed VM Infrastructure**, connecting to Redis caching layers and Prometheus monitoring:

```mermaid
flowchart TB
    subgraph Clients["🌐 BrightEdge Traffic Source"]
        UserReq["API Gateway / External Requests\n(Peak: 2,000 req/sec | 50M req/day)"]
    end

    subgraph Kubernetes["☸️ GCP GKE Cluster (Kubernetes Deployment)"]
        direction TB
        Ingress["Nginx Ingress Controller / Service"]
        
        subgraph PodPool["Pod Pool (HPA Scaled 3 -> 20 Pods)"]
            Pod1["data-sync Pod 1\n(FastAPI :8080)"]
            Pod2["data-sync Pod 2\n(FastAPI :8080)"]
            PodN["data-sync Pod N\n(FastAPI :8080)"]
        end
        
        Config["ConfigMap\n(APP_ENV, LOG_LEVEL, WORKERS)"]
        Secret["Secret\n(REDIS_PASSWORD)"]
        
        PDB["PodDisruptionBudget\n(minAvailable: 1)"]
        HPA["HPA / KEDA Scaler\n(CPU & Request-Rate Driven)"]
    end

    subgraph Observability["📊 Monitoring Stack"]
        SMonitor["ServiceMonitor CRD\n(Scrape /metrics every 30s)"]
        Prometheus["Prometheus Operator\n(release: kube-prometheus-stack)"]
        Grafana["Grafana Dashboards"]
    end

    subgraph VMInfra["🖥️ CentOS/Rocky 8 VM Infrastructure (Ansible Managed)"]
        AnsiblePlay["Ansible Playbook\n(playbook-data-sync.yml)"]
        Role["Ansible Role: be-data-sync\n(Virtualenv @ /srv/data-sync/venv)"]
        Systemd["Systemd Service\n(data-sync.service)"]
    end

    subgraph DataStore["⚡ Caching Layer"]
        RedisCluster[("Redis Cluster / Master\n(Port: 6379)")]
    end

    %% Flow Connections
    UserReq --> Ingress
    Ingress --> PodPool
    Config -. Env Vars .-> PodPool
    Secret -. Auth Password .-> PodPool
    HPA -. Auto Scales .-> PodPool
    
    PodPool -- Fast Cache Read/Write --> RedisCluster
    Pod1 -- /metrics Scrape --> SMonitor
    SMonitor --> Prometheus
    Prometheus --> Grafana

    AnsiblePlay --> Role --> Systemd
    Systemd -- VM Service Cache Connection --> RedisCluster

    classDef k8s fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef vm fill:#fff3e0,stroke:#f57c00,stroke-width:2px;
    classDef obs fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    class K8s,PodPool,Ingress k8s;
    class VMInfra,Systemd vm;
    class Observability,SMonitor,Prometheus obs;
```

---

## 📂 Repository Directory Structure

```
.
├── helm/
│   └── charts/
│       └── data-sync/
│           ├── Chart.yaml                  # Helm v2 Chart metadata
│           ├── values.yaml                 # Safe defaults (Local/Development)
│           ├── values.staging.yaml         # Staging configuration (2 Replicas, INFO log)
│           ├── values.production.yaml      # Production config (HPA min 3 / max 20, strict limits)
│           └── templates/
│               ├── _helpers.tpl            # Template helpers & standard label generators
│               ├── deployment.yaml         # Deployment with probes, securityContext & env vars
│               ├── service.yaml            # ClusterIP Service exposing port 8080
│               ├── configmap.yaml          # ConfigMap for non-sensitive settings
│               ├── secret.yaml             # Opaque Secret for REDIS_PASSWORD
│               ├── hpa.yaml                # HorizontalPodAutoscaler (autoscaling/v2)
│               ├── pdb.yaml                # PodDisruptionBudget (minAvailable: 1)
│               └── servicemonitor.yaml     # Prometheus Operator ServiceMonitor CRD
├── standard/
│   └── data-sync/
│       └── production/
│           ├── kustomization.yaml          # Kustomize overlay referencing Helm base
│           └── deployment-patch.yaml       # GCP Zone topologySpreadConstraint & SECRET_CHECKSUM
├── roles/
│   └── be-data-sync/
│       ├── defaults/main.yml            # Default role variables
│       ├── handlers/main.yml            # Systemd service restart handler
│       ├── tasks/main.yml               # Yum/DNF install, git clone, venv, systemd tasks
│       ├── templates/
│       │   └── data-sync.service.j2    # Jinja2 template for data-sync.service
│       └── meta/main.yml                # Role metadata (CentOS/Rocky EL 8)
├── playbooks/
│   └── playbook-data-sync.yml              # Ansible playbook targeting 'service' group
├── group_vars/
│   └── service.yml                         # Group variables for 'service' VMs
├── DESIGN.md                               # Architectural design document (Scaling, Isolation, Secrets)
└── README.md                               # Platform documentation & operational guide
```

---

## ⚙️ Environment Configuration Matrix

The table below outlines how configuration values are mapped across different environments:

| Parameter | Development (`values.yaml`) | Staging (`values.staging.yaml`) | Production (`values.production.yaml`) |
| :--- | :--- | :--- | :--- |
| **Replicas** | `1` (Fixed) | `2` (Fixed) | `3` Min / `20` Max (HPA Enabled) |
| **Log Level** | `DEBUG` | `INFO` | `INFO` |
| **CPU Request / Limit** | `100m` / `250m` | `250m` / `500m` | `500m` / `1000m` |
| **Memory Request / Limit**| `128Mi` / `256Mi` | `256Mi` / `512Mi` | `512Mi` / `1Gi` |
| **Redis Host** | `redis-master.data-sync.svc.cluster.local` | `redis-staging.data-sync.svc.cluster.local` | `redis-prod.data-sync.svc.cluster.local` |
| **HPA Target CPU** | Disabled | Disabled | `70%` Target Utilization |
| **Zone Spreading** | Default Kubernetes Scheduling | Default Kubernetes Scheduling | Enforced via Kustomize `topologySpreadConstraint` |

---

## ☸️ Part 1: Helm Chart & Kustomize Deployment

### 1. Helm Chart Linting & Validation

To validate the Helm chart syntax and structure locally:

```bash
# Lint the Helm chart for syntax correctness
helm lint helm/charts/data-sync
```

To render and inspect standard Kubernetes manifests for each environment:

```bash
# Preview Development manifests
helm template data-sync helm/charts/data-sync

# Preview Staging manifests
helm template data-sync helm/charts/data-sync -f helm/charts/data-sync/values.staging.yaml

# Preview Production manifests
helm template data-sync helm/charts/data-sync -f helm/charts/data-sync/values.production.yaml
```

---

### 2. Staging Deployment Workflow

> [!NOTE]
> Ensure your active `kubectl` context points to the target Staging cluster.

```bash
# 1. Create Staging Namespace if it doesn't exist
kubectl create namespace data-sync-staging --dry-run=client -o yaml | kubectl apply -f -

# 2. Deploy / Upgrade data-sync in Staging
helm upgrade --install data-sync helm/charts/data-sync \
  --namespace data-sync-staging \
  -f helm/charts/data-sync/values.staging.yaml \
  --set secret.redisPassword="$STAGING_REDIS_PASSWORD" \
  --wait
```

---

### 3. Production Deployment Workflow

#### Option A: Direct Helm Deployment
```bash
# 1. Create Production Namespace
kubectl create namespace data-sync-prod --dry-run=client -o yaml | kubectl apply -f -

# 2. Deploy / Upgrade data-sync in Production
helm upgrade --install data-sync helm/charts/data-sync \
  --namespace data-sync-prod \
  -f helm/charts/data-sync/values.production.yaml \
  --set secret.redisPassword="$PROD_REDIS_PASSWORD" \
  --wait
```

#### Option B: Production Kustomize Overlay Deployment
The production overlay applies GCP zone spreading (`topologySpreadConstraint`) and automatic secret rollout triggers (`SECRET_CHECKSUM`).

```bash
# Preview Production Kustomize Overlay Output
kubectl kustomize standard/data-sync/production

# Apply Production Overlay to GKE Cluster
kubectl kustomize standard/data-sync/production | kubectl apply -n data-sync-prod -f -
```

---

## 🔧 Part 2: Ansible VM Infrastructure (`be-data-sync`)

### Ansible Provisioning Architecture

```mermaid
sequenceDiagram
    autonumber
    participant Admin as 💻 Ansible Control Node
    participant VM as 🖥️ CentOS/Rocky 8 VM
    participant Git as 📦 Git Repository
    participant Systemd as ⚙️ Systemd Manager

    Admin->>VM: Execute playbook-data-sync.yml (tags: install, deploy)
    Note over VM: Filter execution (be_role == 'service')
    VM->>VM: 1. Install Python 3.9, pip, git via Yum/DNF
    VM->>Git: 2. Clone / Update repo to /srv/data-sync
    VM->>VM: 3. Create virtualenv at /srv/data-sync/venv
    VM->>VM: 4. Install requirements.txt via pip
    Admin->>VM: 5. Render Jinja2 template (data-sync.service.j2)
    VM->>Systemd: 6. Deploy /etc/systemd/system/data-sync.service
    VM->>Systemd: 7. Trigger Handler: Restart & Enable data-sync service
    Systemd-->>Admin: ✔ Service Active & Running on Port 8080
```

### Execution Commands

```bash
# 1. Run Playbook Syntax Check
ansible-playbook playbooks/playbook-data-sync.yml --syntax-check

# 2. Run Ansible-Lint
ansible-lint playbooks/playbook-data-sync.yml roles/be-data-sync/

# 3. Deploy full installation on 'service' host group
ansible-playbook -i inventory.ini playbooks/playbook-data-sync.yml --tags "install,deploy"

# 4. Deploy configuration update only
ansible-playbook -i inventory.ini playbooks/playbook-data-sync.yml --tags "deploy"
```

---

## 📐 Part 3: Architectural Design Highlights (`DESIGN.md`)

The comprehensive design document [DESIGN.md](file:///c:/Users/ROHIT/Desktop/Devops%20task%20Brightedge/DESIGN.md) addresses high-scale challenges (50M req/day, 2000 req/s burst):

> [!IMPORTANT]
> **Sub-20s Scale-Out Lag**: Solved by implementing **KEDA (Kubernetes Event-driven Autoscaling)** using HTTP request rate leading metrics, aggressive HPA step-up scaling, GKE Image Streaming, and scheduled baseline pre-warming.

> [!TIP]
> **Noisy Neighbour Workload Isolation**: Solved using dedicated GKE node pools (`api-pool`), Node Taints & Tolerations (`workload=data-sync:NoSchedule`), Node Affinity, `Guaranteed` QoS class (Static CPU Manager), and `PriorityClasses`.

> [!WARNING]
> **Zero-Downtime Secret Rotation**: Solved using dual-password authentication in Redis & FastAPI, External Secrets Operator / Reloader delivery, rolling update strategy (`maxUnavailable: 0`), and active health verification.

