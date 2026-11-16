# 04. Software Requirements Specification (SRS): LaundryMann 2.0
*(Structured after IEEE 29148 / 830 practice.)*

## 1. Introduction
**1.1 Purpose.** Specify testable requirements for LaundryMann 2.0. **1.2 Scope.** Web API + PWA + ML inference for garment analysis and wash planning. **1.3 Definitions.** See PD glossary. **1.4 References.** Docs 01-18; ISO 3758 (care symbols); OWASP ASVS and API Top 10 (2023).

## 2. Overall description
**2.1 Product perspective.** Self-hosted web system: React PWA ↔ FastAPI ↔ PostgreSQL + object store; inference in-process via ONNX Runtime.
**2.2 User classes.** Anonymous visitor (landing only), Registered user, Admin (ops only).
**2.3 Operating environment.** Server: Linux, Docker, Python 3.12, 4+ vCPU, 8 GB RAM. Client: evergreen Chrome/Edge/Safari/Firefox with camera access.
**2.4 Constraints.** See PD §7b.
**2.5 Assumptions.** Photo taken indoors with garment mostly in frame.

## 3. Functional requirements

| ID | Requirement (shall) | Pri | Verification |
|---|---|---|---|
| FR-01 | Register, login, refresh, logout with the session spec in Security Plan S2 | M | Test, Inspection |
| FR-02 | Accept an image ≤ 8 MB (JPEG/PNG/WebP), validate by magic bytes, re-encode, strip EXIF | M | Test |
| FR-03 | Detect and segment garments; return mask, box, category (13 DeepFashion2 categories) | M | Test (ML) |
| FR-04 | Compute dominant colours in CIELAB from the garment mask; return colour family (white, light, pastel, bright, dark, multi) and bleed-risk class | M | Test |
| FR-05 | Estimate fabric family with calibrated probability; return "unknown" when the conformal set has > 2 classes or top prob < threshold | M | Test (ML) |
| FR-06 | Localise stains (boxes/masks); allow user to set stain type from a fixed list; store type | M | Test |
| FR-07 | Read care label: OCR text (fibre %, keywords) + detect ISO 3758 symbols; convert to structured constraints | M | Test |
| FR-08 | Produce a wash plan (mode, temperature, detergent class, spin, bleach allowed, dry method, ironing) with ordered reasons and warnings, honouring hard constraints | M | Test (property) |
| FR-09 | Given ≥ 2 analysed items, partition into the minimum number of safe loads via conflict graph; explain each split | S | Test |
| FR-10 | CRUD wardrobe items, owner-scoped; list with pagination | S | Test |
| FR-11 | Accept user correction of any predicted attribute; store with model version; opt-in flag for reuse | S | Test |
| FR-12 | Export a PDF wash guide for an analysis or load plan | C | Test |
| FR-13 | Provide history and statistics computed from stored records only (no fabricated numbers) | C | Inspection |
| FR-14 | Admin endpoints: list model versions, activate a version (hash verified), health, metrics | S | Test |
| FR-15 | `GET /me/export`, `DELETE /me` | M | Test |

## 4. External interface requirements
**4.1 UI:** Doc 10. **4.2 API:** `openapi.yaml`, base path `/api/v1`, JSON + multipart for images, errors as `application/problem+json`. **4.3 Hardware:** camera via browser `getUserMedia`; no other hardware. **4.4 Software:** PostgreSQL 16, ONNX Runtime, optional PaddleOCR/Tesseract, WeasyPrint/ReportLab for PDF. **4.5 Communications:** HTTPS/TLS 1.2+.

## 5. Non-functional requirements

| ID | Category | Requirement | Measure |
|---|---|---|---|
| NFR-P1 | Performance | Single-garment analysis p95 ≤ 2.0 s (CPU 8 vCPU) *(proposed)* | Locust |
| NFR-P2 | Performance | Basket (≤ 12 items) p95 ≤ 6 s *(proposed)* | Locust |
| NFR-P3 | Capacity | 10 concurrent users without errors; excess gets 429/503 with Retry-After | Locust |
| NFR-R1 | Reliability | Readiness endpoint false until all models load; no request served with a missing model | Test |
| NFR-R2 | Reliability | Any model failure yields a "cannot analyse" problem response, never a fabricated default such as "Cotton (Fallback)" | Test |
| NFR-S1 | Safety | 0 hard-constraint or never-do violations across 10,000 fuzzed plans | Property test |
| NFR-SEC1 | Security | Meets Security Plan; ASVS L1 complete, L2 for V2-V5, V8 | Audit |
| NFR-SEC2 | Security | 0 High/Critical from ZAP, Bandit, pip-audit, Trivy at release | CI |
| NFR-A1 | Accuracy | Meets PD §7 targets on frozen test and field sets | Eval harness |
| NFR-A2 | Calibration | ECE ≤ 0.05; conformal coverage 90% ± 3 | Eval harness |
| NFR-U1 | Usability | WCAG 2.2 AA; task success ≥ 90% | axe + user test |
| NFR-M1 | Maintainability | Clean clone → running in ≤ 15 min; coverage ≥ 85% core / 95% engine; no duplicated modules | CI |
| NFR-M2 | Portability | Runs via `docker compose` on Linux/macOS/Windows (WSL2) | Test |
| NFR-O1 | Observability | JSON logs, request IDs, Prometheus metrics, model version in every response header | Test |
| NFR-D1 | Data | Images retained ≤ 90 days by default; deletion cascades to files | Test |
| NFR-L1 | Legal | Dataset registry complete; no dataset used without recorded licence | Inspection |

## 6. Data requirements
Logical model in doc 09. Images stored outside DB; DB stores metadata and derived attributes. All timestamps UTC. All ids UUIDv4.

## 7. Traceability matrix (excerpt; full matrix maintained in `docs/qa/rtm.csv`)

| Business req | SRS req | Design element | Test |
|---|---|---|---|
| BR-01 | FR-02..08 | `AnalysisService` | E2E-01, IT-analyze-* |
| BR-02 | FR-07, FR-08, NFR-S1 | `DecisionEngine`, `ConstraintSet` | PT-engine-hard-constraints |
| BR-03 | FR-05, FR-11 | `Calibrator`, `CorrectionSheet` | ML-calib-01, E2E-04 |
| BR-04 | FR-09 | `LoadPlanner` | UT-planner-* |
| BR-05 | FR-15, NFR-D1, SEC | `PrivacyService` | IT-export, IT-delete |
| BR-06 | NFR-M1 | Docker/Make/CI | CI-clean-clone |
| BR-07 | NFR-A1/A2 | Eval harness | ML-* |

## 8. Acceptance
System accepted when all Must requirements pass verification, no S1/S2 open, and traceability matrix has no orphan requirement.
