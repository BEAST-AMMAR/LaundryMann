# 15. Test Plan: LaundryMann 2.0

## Part A. Scope and objectives
Verify every requirement in the SRS, prove the safety properties, and measure the ML components honestly on data they never saw. Covers unit, integration, contract, E2E, ML evaluation, security, performance, accessibility.

## Part B. LaundryMann-specific test design

### B1. Decision-engine tests (safety-critical)
| ID | Test | Type | Expected |
|---|---|---|---|
| PT-engine-01 | Random `ItemState` (hypothesis, 10k) → plan | Property | `plan.temp_c ≤ label.max_wash_temp_c` whenever label present |
| PT-engine-02 | Random states with fabric ∈ {silk, wool, unknown} | Property | Bleach never `any`; no chlorine |
| PT-engine-03 | Any protein/blood stain | Property | `temp_c ≤ 30` |
| PT-engine-04 | `dry_clean_only=true` | Property | No home-wash plan; excluded from loads |
| PT-engine-05 | Every plan | Property | `reasons` non-empty and each cites a rule id |
| GT-engine-* | 50 golden scenarios reviewed by a knowledgeable person | Golden | Exact plan match |
| MT-engine | mutmut on rules/engine | Mutation | Survivors < 10% |

### B2. Load planner
`UT-planner-01` no conflicting pair shares a load (hypothesis); `UT-planner-02` deterministic output; `UT-planner-03` white+red separated; `UT-planner-04` capacity respected; `UT-planner-05` dry-clean items excluded.

### B3. Colour analyser
Boundary tests at L*/C* thresholds; shadowed white must remain "white"; denim blue = "dark"; stripes = "multi"; invariance to brightness ±20% (family unchanged for ≥ 95% of validation samples).

### B4. Image intake / API
`IT-upload-bomb`, `IT-upload-polyglot`, `IT-upload-wrong-magic`, `IT-upload-oversize`, `IT-exif-stripped`, `IT-idempotency-key`, `IT-owner-scope-*`, `IT-jwt-*`, `IT-rate-limit-login`, `IT-ready-gate` (models absent → `503` and never a fabricated "Cotton (Fallback)").

### B5. Privacy
`IT-export-complete`, `IT-delete-cascade-files`, `IT-retention-job`, `IT-corrections-opt-in-default-off`.

### B6. End-to-end (Playwright, Chromium + WebKit)
`E2E-01` register → upload sample garment → see plan. `E2E-02` low-confidence path → choose fabric → plan updates. `E2E-03` label scan lowers temperature with visible explanation. `E2E-04` correction saved. `E2E-05` basket → two loads with reasons. `E2E-06` delete account.

## Part C. ML evaluation protocol (LaundryMann)

| Model | Frozen test | Field set | Primary metrics | Acceptance (proposed) |
|---|---|---|---|---|
| Garment seg. | DeepFashion2 val subset | 100 pile/garment photos | mAP@0.5, instance recall | ≥ 0.70 / ≥ 0.85 |
| Colour | Fashion Product Images subset (baseColour → 6 families) | 300 phone photos with human label | Top-1, confusion matrix | ≥ 90% / ≥ 80% |
| Stain detector | FabricSpotDefect original test split | Field stains (tea, curry, oil, ink) | mAP@0.5, recall, FP/image | ≥ 0.60 / ≥ 0.70 / ≤ 0.5 |
| Fabric | TextileNet/FabricClassv2 held-out (group split) | 200 garments with label ground truth | Macro-F1, ECE, selective acc. | ≥ 0.70, ≤ 0.05, ≥ 90% @ 50% cov. |
| Care symbols | Synthetic + Kaggle comp. test | 100 real labels | Per-category acc. | ≥ 90% / ≥ 75% |
| OCR | n/a | 100 real labels | Field-level accuracy (temp, fibre %) | ≥ 80% |

**Baselines always reported:** v1 colour CNN, v1 stain detector (YOLOv8n 6-epoch), majority class.
**Slice report:** lighting, background, phone model, fabric, colour family. **Failure gallery** committed per release.
**Calibration report:** reliability diagram, ECE, conformal coverage, risk-coverage curve.

## Part D. Non-functional tests
Performance (Locust per T4) with p95 ≤ 2.0 s single garment at 10 users; accessibility (axe + manual keyboard/screen reader); security per Security Plan S13; compatibility (Chromium, WebKit, Firefox; Android and iOS phones).

## Part E. Traceability of tests to requirements
Maintained in `docs/qa/rtm.csv`; CI fails if any Must requirement lacks at least one passing test id.

## Part F. Common testing standard
## T1. Test pyramid and scope

| Level | Share of tests | Tools | What it proves |
|---|---|---|---|
| Unit | ~70% | pytest, hypothesis, Vitest | Pure logic (decision engine, grouping, shelf-life math, validators) |
| Integration | ~20% | pytest + Testcontainers/PostgreSQL, httpx `AsyncClient` | Routes ↔ DB ↔ storage ↔ inference wrapper |
| Contract | CI job | schemathesis against OpenAPI | API matches its spec, no 500s on fuzzed input |
| End-to-end | ~5% | Playwright | Real user journeys in a browser |
| ML evaluation | Scheduled + on model change | Eval harness, `pytest -m ml` | Model quality, calibration, slice performance |
| Non-functional | Pre-release | locust, axe-core, ZAP | Performance, accessibility, security |

## T2. ML test protocol (applies to every model)

1. **Frozen test sets**: stored as manifest files with per-file SHA-256; a CI check fails if a test file appears in any training manifest.
2. **Leakage guards**: (a) split by *source image*, never by augmented copy; (b) near-duplicate removal with perceptual hashing (pHash Hamming distance ≤ 6) across splits; (c) group-aware split where a group = same product/scene/photographer session.
3. **Baselines**: majority-class, a trivial heuristic, and the **legacy model** are always reported next to the new model.
4. **Metrics**: per-class precision/recall/F1, confusion matrix, macro-F1, calibration (ECE, reliability diagram), selective accuracy vs coverage (risk–coverage curve), abstention rate.
5. **Slices**: lighting (bright/dim/warm), background (studio/cluttered), camera (2+ phones), resolution, item/fabric/colour class. A slice more than 10 points below average is a release blocker or a documented limitation.
6. **Invariance and directional tests** (behavioural testing): brightness ±20%, small rotation, JPEG quality 60–95 must not change the top prediction on ≥ 95% of clean samples; adding an obvious stain/rot region must not *reduce* the stain/spoiled score.
7. **Field test set**: a small, real, phone-photo set collected by you (protocol in the Dataset Plan). Never used for training or threshold tuning except the final one-time calibration split described there.
8. **Regression**: every model release must not be worse than the previous on any *safety* metric (spoiled-recall, hard-constraint violations).
9. **Reproducibility**: seed, library versions, dataset manifest hash, and git commit stored with each run (MLflow).

## T3. Test data management

Fixtures under `tests/fixtures/` (tiny, synthetic, licence-clean). Real dataset images are never committed. Golden JSON outputs for the decision engine are versioned and reviewed like code.

## T4. Performance test approach

Locust scenarios: (1) 10 concurrent users analysing images for 5 min; (2) spike to 50 users for 1 min; (3) soak 30 min. Record p50/p95/p99, error rate, CPU/RAM. Baseline measured **before** SLOs are finalised in Phase 0.

## T5. Accessibility and usability testing

axe-core in Playwright for every page; manual keyboard-only run; screen-reader smoke test (NVDA/VoiceOver) for the scan flow; 5-person hallway usability test per major release with the task list in the UX doc.

## T6. Exit criteria (per release)

No open S1/S2; ≥ 95% of planned tests executed and passing; coverage targets met; ML acceptance table met (or documented waiver); security gates clean; traceability matrix has no requirement without a passing test.
