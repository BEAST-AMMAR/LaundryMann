# 07. Software Architecture Document (SAD): LaundryMann 2.0

## 1. Architectural drivers

| Driver | Consequence |
|---|---|
| Safety (no harmful advice) | Perception separated from decision; hard constraints in a dedicated, heavily tested layer |
| Trustworthy uncertainty | Calibration + abstention are first-class components, not afterthoughts |
| Solo maintainability | Modular monolith, not microservices |
| Privacy | Local inference, private storage, retention jobs |
| Reproducibility | Everything containerised, models and data hashed |

## 2. Context view (C4 level 1)

```mermaid
flowchart LR
  U[User on phone/desktop] -->|HTTPS| W[LaundryMann PWA]
  W -->|REST /api/v1| A[LaundryMann API]
  A --> DB[(PostgreSQL)]
  A --> OS[(Object store: images)]
  A --> M[[ONNX models]]
  Adm[Admin/Developer] --> A
  Adm --> ML[MLflow + Streamlit ML dashboard]
  ML -.reads manifests/metrics.-> DS[(Dataset registry)]
```

## 3. Container view (C4 level 2)

```mermaid
flowchart TB
  subgraph Client
    PWA[React PWA + service worker]
  end
  subgraph Server
    GW[Caddy reverse proxy: TLS, size limits]
    API[FastAPI app]
    subgraph API_internal[API modules]
      R[Routers]
      S[Services]
      Repo[Repositories owner-scoped]
      P[Perception adapters]
      D[Decision engine + rules]
      C[Calibration/abstention]
    end
    DB[(PostgreSQL)]
    OBJ[(MinIO / volume)]
  end
  PWA --> GW --> API
  R --> S --> Repo --> DB
  S --> P --> C
  S --> D
  S --> OBJ
```

## 4. Component responsibilities

| Component | Responsibility | Depends on | Notes |
|---|---|---|---|
| `routers/*` | HTTP, auth dependency, schema validation | services | No business logic |
| `AuthService` | Register/login/refresh/revoke | UserRepo, TokenRepo | Argon2id, JWT |
| `ImageService` | Validate, sanitise, store, sign URLs | ObjectStore | Security S4 |
| `AnalysisService` | Orchestrate perception → state → plan | perception, decision | Idempotent per image hash |
| `GarmentDetector` | Segment garments | ONNX | Interface `Detector` |
| `ColourAnalyzer` | LAB palette, family | numpy/OpenCV | Pure functions |
| `FabricClassifier` | Fabric probs + conformal set | ONNX, Calibrator | Returns `unknown` |
| `StainDetector` | Tiled stain detection | ONNX | |
| `CareLabelReader` | OCR + symbols → constraints | OCR, ONNX | Strictness merge |
| `Calibrator` | Temperature + conformal | fitted params file | Versioned with model |
| `DecisionEngine` | Constraints + rules → plan | rules YAML | Pure, deterministic |
| `LoadPlanner` | Conflict graph → loads | DecisionEngine | Pure |
| `WardrobeService` | CRUD | Repos | |
| `PrivacyService` | Export, delete, retention | Repos, ObjectStore | Scheduled job |
| `ModelRegistry` | Load, verify hash, expose versions | filesystem | Readiness gate |

## 5. Key runtime sequence: analyse a garment

```mermaid
sequenceDiagram
  participant U as User (PWA)
  participant G as Gateway
  participant R as Router
  participant A as AnalysisService
  participant I as ImageService
  participant P as Perception
  participant D as DecisionEngine
  participant DB as Postgres
  U->>G: POST /api/v1/analyses (image, Bearer)
  G->>R: size-limited request
  R->>R: authenticate + validate
  R->>A: analyze(user, image)
  A->>I: sanitise + store
  I-->>A: image_id
  A->>P: detect garment (mask)
  par in parallel
    A->>P: colour (mask)
    A->>P: fabric (crop)
    A->>P: stains (tiles)
  end
  P-->>A: attributes + calibrated confidence
  A->>D: plan(ItemState + constraints)
  D-->>A: plan + reasons + warnings
  A->>DB: save analysis (model versions)
  A-->>U: 201 result JSON
```

## 6. Deployment view

Single host (VPS) running compose: `caddy`, `api`, `db`, `minio`. TLS at Caddy; internal network only for db/minio; api container non-root with read-only FS and a tmpfs for scratch. Scale path: run 2+ API replicas behind Caddy; move inference to a separate worker only if CPU contention appears (measured).

## 7. Quality attribute tactics

| Attribute | Tactic |
|---|---|
| Safety | Hard-constraint layer, never-do rules, property tests, mutation testing on engine |
| Security | Threat model (doc 14), owner-scoped repositories, upload sanitiser, ONNX only |
| Performance | ONNX Runtime, int8/fp16, parallel stages, image downscale, tiling only for stain stage |
| Reliability | Readiness gate, timeouts, circuit-breaker on OCR, graceful "cannot analyse" |
| Maintainability | Interfaces around models, pure decision code, single rules file, ADRs |
| Testability | Dependency injection for models (fakes in tests), golden scenarios |
| Observability | Structured logs, metrics, model-version headers |

## 8. Data architecture
Relational metadata (doc 09); images in object store; rule sets and models on filesystem with hashes; dataset manifests in git (no images). Retention job deletes expired images and their rows.

## 9. Technical-debt elimination map (v1 → v2)

| v1 structure | v2 replacement |
|---|---|
| `app.py` (Tkinter), `src/app.py`, `streamlit_app.py`, `frontend/` | `apps/web` React PWA (+ dev-only Streamlit) |
| `models.py` w/ 3 models loaded in a background thread | `ModelRegistry` + readiness gate |
| `decision_engine.py` if/else + bins A-G | `DecisionEngine` + YAML rules + hard/soft separation |
| 3 copies of recipe table | one `rules/wash_plans.yaml` |
| `auth.py` (SHA-256) + cookie username | `AuthService` (Argon2id, JWT, rotating refresh) |
| Weights committed to git | Release assets / HF Hub / DVC; hashes in registry |
| `Dockerfile` with Jupyter | Multi-stage non-root app image |

## 10. Risks to the architecture
Model size vs CPU budget (mitigate: quantise, smaller backbones); OCR variability (mitigate: user-assisted crop); AGPL (ADR-04). See Risk Register.
