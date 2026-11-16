# 06. Technical Requirements Document (TRD): LaundryMann 2.0

## 1. Technology stack and reasons

| Layer | Choice | Why (and what it replaces) |
|---|---|---|
| Language | Python 3.12 | Current ecosystem; v1 used Python 3.9-era pins (torch 2.0.1, streamlit 1.25) |
| Env/deps | `uv` + lockfile (hashes) | Reproducible, fast; v1 had unpinned/inconsistent requirements |
| API | FastAPI + Pydantic v2 | Typed schemas, OpenAPI for free; v1 API had no auth/validation |
| ORM/migrations | SQLAlchemy 2.x + Alembic | Versioned schema; v1 used ad-hoc SQLite |
| DB | PostgreSQL 16 (SQLite only for unit tests) | Constraints, JSONB, concurrency |
| Inference | ONNX Runtime (CPU) | No pickle risk; fast CPU serving; hardware independent |
| Training | PyTorch 2.x + Ultralytics (detector) + timm (classifier) | Standard, reproducible |
| Detector | YOLO26-seg (Ultralytics) | Released Jan 2026; NMS-free, CPU-friendly; **AGPL-3.0**. Alternative: RF-DETR (Apache-2.0), see ADR-04 |
| Classifier backbone | Pretrained ConvNeXt-tiny / EfficientNet-B0 / DINO-family ViT-S, chosen by benchmark in Phase 2 | Transfer learning beats scratch CNNs on small data |
| OCR | PaddleOCR (primary), Tesseract (fallback) | Handles tiny label text better than Tesseract alone |
| Calibration | Temperature scaling + split conformal (own implementation, ~100 lines) | Honest confidence; abstention |
| Experiment tracking | MLflow (local) + dataset manifests hashed | Reproducibility |
| Front-end | React + Vite + TypeScript + Tailwind, TanStack Query, PWA (service worker) | One UI instead of four |
| Internal ML dashboard | Streamlit (dev-only) | Keeps your Streamlit skills; not the product UI |
| Jobs | In-process `anyio` thread/process pool; Redis only if scaling | Avoid needless infra |
| Reverse proxy | Caddy (auto-TLS) | Simple HTTPS |
| Observability | structlog, Prometheus client, Grafana (optional) | NFR-O1 |
| CI/CD | GitHub Actions | Free for public repos |
| Quality | ruff, mypy --strict (core), pre-commit, pytest, hypothesis, schemathesis, Playwright, Locust | Test Plan |
| Containers | Docker multi-stage, non-root | Security Plan S7 |

*Version policy:* pin the current stable version at project start via lockfile; upgrade monthly through Renovate PRs.

## 2. Model specifications

| Model | Task | Input | Output | Training data | Deployment format |
|---|---|---|---|---|---|
| G-Det | Garment detect+segment | 640 px | boxes, masks, 13 classes | DeepFashion2 (+ field set finetune) | ONNX (int8/fp16 variants) |
| S-Det | Stain detect | 640 px tiles w/ overlap | boxes + score | FabricSpotDefect originals + own field | ONNX |
| F-Cls | Fabric family | 224-288 px crop of garment/patch | 7-way probs + conformal set | TextileNet subset + FabricClassv2 + own | ONNX |
| L-Det | Care-label region | 640 px | box | Own + Kaggle care-symbol comp. + synthetic | ONNX |
| Sym-Cls | ISO 3758 symbols | 96-128 px crop | symbol id + level | Synthetic renders + real crops | ONNX |
| Colour | (no ML) | mask pixels | palette/family | none; validated on Fashion Product Images | Python code |

Model card per model (`docs/model_cards/*.md`): intended use, data, metrics per slice, calibration, limitations, licence, hash.

## 3. Training specification (per model, Phase 2)
* **Splits:** group-aware, dedup by pHash; 70/15/15; frozen `test` manifest.
* **Transfer learning recipe:** (1) linear probe 3-5 epochs; (2) unfreeze last stages with layer-wise LR decay; (3) label smoothing 0.05-0.1; (4) augmentations: colour jitter *mild for fabric* (colour is not the signal for fibre), random resized crop, blur, JPEG, lighting; **no flips that change label semantics** (text/symbols).
* **Detectors:** Ultralytics defaults + mosaic; imgsz 640; early stopping on val mAP; epochs ≥ 50 (v1 stopped at 6).
* **Calibration:** fit temperature on validation set; conformal quantile on a separate calibration split.
* **Budget:** each run ≤ 2 GPU-hours on free tiers; log to MLflow.
* **Export:** ONNX opset current; verify numerical parity (max abs diff < 1e-3) vs PyTorch; benchmark CPU latency.

## 4. Performance budget (proposed, re-baselined in Phase 0)

| Stage | Budget (CPU 8 vCPU) |
|---|---|
| Upload + validate + re-encode | ≤ 150 ms |
| G-Det | ≤ 350 ms |
| Colour | ≤ 60 ms |
| F-Cls | ≤ 120 ms |
| S-Det (tiled) | ≤ 500 ms |
| Care label (only if provided) | ≤ 600 ms |
| Decision engine | ≤ 20 ms |
| Serialisation | ≤ 50 ms |
| **Total (garment + stain + fabric)** | **≤ 1.3 s typical, p95 ≤ 2.0 s** |

Stages run in parallel where independent (S-Det, F-Cls after G-Det).

## 5. Infrastructure

```
docker-compose.yml
  web     (nginx/caddy serving PWA build)
  api     (FastAPI + ONNX Runtime; 2 workers)
  db      (postgres:16)
  minio   (S3-compatible object store)  # or local volume in dev
  mlflow  (dev profile only)
```
Environments: local, ci, staging, prod (demo). Config via env vars only. Health: `/health/live`, `/health/ready`. Backups: nightly `pg_dump` + object store snapshot; restore drill before v1.0.

## 6. Repository layout

```
laundrymann/
  apps/api/           # FastAPI app (routers, services, repositories, schemas)
  apps/web/           # React PWA
  packages/ml/        # inference wrappers, calibration, decision rules
  training/           # training scripts, configs, dataset builders
  datasets/           # REGISTRY.md, manifests (hashes), scripts (no images)
  rules/              # YAML rule sets (versioned) + golden scenarios
  docs/               # this pack, model cards, ADRs
  tests/              # unit, integration, e2e, ml, security
  deploy/             # compose, Caddyfile, CI helpers
  Makefile  pyproject.toml  uv.lock  .pre-commit-config.yaml
```

## 7. Architecture Decision Records (summary)

| ADR | Decision | Reason | Consequence |
|---|---|---|---|
| 01 | Colour by classical LAB analysis, not CNN | Measurement, avoids circular labels | Needs good masks |
| 02 | Foundation-model transfer, not scratch CNN | Data-efficient | Bigger models → ONNX/quantise |
| 03 | Rule engine data-driven (YAML) with hard/soft separation | Explainable, auditable | Need rule test tooling |
| 04 | YOLO26 now; RF-DETR as licence-safe swap | AGPL risk | Keep detector behind interface |
| 05 | One PWA; Streamlit dev-only | Reduce surface | Rewrite UI once |
| 06 | Abstain over guess | Safety | Some "Not sure" results |
| 07 | ONNX for serving | Security + speed | Export/parity tests |
| 08 | Drop fake sensors | Honesty | Smaller pitch, higher trust |

## 8. Configuration matrix (selected)

| Key | Default | Notes |
|---|---|---|
| `MAX_UPLOAD_MB` | 8 | Proxy + app |
| `MAX_PIXELS` | 40_000_000 | Bomb guard |
| `ABSTAIN_MIN_PROB` | 0.55 | Tuned on val, frozen |
| `CONFORMAL_ALPHA` | 0.10 | 90% coverage |
| `IMAGE_RETENTION_DAYS` | 90 | Privacy |
| `INFERENCE_CONCURRENCY` | 2 | Backpressure |
| `RATE_LIMIT_LOGIN` | 5/min | Security |

## 9. Compatibility and licensing
Client: latest two versions of major browsers. Licences: repo MIT/Apache for own code where dependency licences allow; Ultralytics AGPL noted; datasets per registry; model weights derived from restricted datasets are marked **research-only** in model cards.
