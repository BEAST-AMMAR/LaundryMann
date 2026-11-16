# 16. Quality Assurance Plan (QAP): LaundryMann 2.0

## 1. Purpose and scope
Define how quality is planned, built-in, measured, and enforced for LaundryMann 2.0 across code, models, data, security, and documentation.

## 2. Quality standards and references
IEEE 29148 (requirements), ISO/IEC 25010 (quality model: functional suitability, performance efficiency, compatibility, usability, reliability, security, maintainability, portability), OWASP ASVS/API Top 10, WCAG 2.2 AA.

## 3. Quality goals mapped to ISO/IEC 25010

| Characteristic | Goal | Evidence |
|---|---|---|
| Functional suitability | Correct, complete plans | Golden + property tests |
| Performance efficiency | p95 ≤ 2.0 s | Locust report |
| Compatibility | Major browsers | Playwright matrix |
| Usability | ≥ 90% task success, AA | User test + axe |
| Reliability | No fabricated defaults; readiness gate | IT tests |
| Security | 0 High/Critical | Scan reports |
| Maintainability | No duplicate modules; ≥ 85% coverage | CI |
| Portability | Docker on 3 OSes | CI matrix |
| Safety (extension) | 0 hard-rule violations | Property + mutation |

## 4. Traceability matrix (excerpt)

| Req | Design | Test IDs | Status |
|---|---|---|---|
| FR-01 | AuthService | IT-jwt-*, T1-T3 tests | Planned |
| FR-02 | ImageService | IT-upload-* | Planned |
| FR-04 | ColourAnalyzer | UT-colour-*, ML-colour | Planned |
| FR-05 | Calibrator | ML-fabric-calib, UT-abstain | Planned |
| FR-07 | CareLabelReader | ML-symbols, UT-merge-strict | Planned |
| FR-08 | DecisionEngine | PT-engine-*, GT-engine-* | Planned |
| FR-09 | LoadPlanner | UT-planner-* | Planned |
| FR-15 | PrivacyService | IT-export, IT-delete | Planned |
| NFR-P1 | Pipeline | Locust | Planned |
| NFR-SEC1/2 | All | ZAP, Bandit, pip-audit, Trivy | Planned |

## 5. ML/data quality assurance (LaundryMann-specific)
* **Dataset QA:** registry entry, licence verified, hash recorded, class balance report, duplicate report, label-noise spot check of 100 random samples per dataset (record error rate).
* **Model QA gates:** metrics ≥ acceptance; slice gaps ≤ 10 pts (or documented); ECE ≤ 0.05; ONNX parity; latency budget; model card present; no regression on safety metrics.
* **Rule QA:** each rule has a cited source, an example scenario, and a reviewer initial; rule changes bump the version and re-run golden tests.

## 6. Process and standards
Trunk-based with short branches; PR template with checklist (Q6 below); conventional commits; semantic versioning; ADRs for decisions; changelog.

## 7. Audit checkpoints

| Checkpoint | When | Auditor | Output |
|---|---|---|---|
| Requirements review | End P0 | Mentor/peer | Signed-off SRS |
| Design review | End P1 | Peer | ADR approvals |
| Model review | End P2a/P2b | Self + peer | Model cards, failure galleries |
| Rule review | Before P3 exit | Domain-knowledgeable person | Rule sign-off |
| Security review | P4 | Self + external checklist | Pen-test checklist result |
| Release readiness | P4 | Self | Release checklist |

## 8. Supplier / third-party control
Datasets and models are "suppliers": registered, licence-checked, hashed, and re-verified on update. Dependencies through lockfile and Renovate.

## 9. Common QA standard
## Q1. Quality objectives

1. **Truthfulness**: every number in README/docs is reproducible by a script in the repo (`make reproduce-metrics`). No unmeasured claim ships.
2. **Safety**: the system never gives advice that contradicts a hard constraint (care label / food-safety rule) and abstains when uncertain.
3. **Reliability**: a clean clone builds, tests pass, and the app runs with one command (`docker compose up`).
4. **Maintainability**: one source of truth per concept (no duplicate `train.py`, no three copies of the wash-cycle table).

## Q2. Roles (solo developer wearing hats)

| Role | Responsibility | Mitigation for being one person |
|---|---|---|
| Developer | Implement, unit-test | Pre-commit + CI gates |
| Reviewer | Review every PR | Self-review with checklist (Q6) + one external reviewer (mentor/friend) for security-sensitive PRs |
| QA lead | Owns this plan, test reports | Templates in `docs/qa/` |
| ML evaluator | Owns eval harness and dataset registry | Frozen test sets, hash-checked, never used for tuning |
| Release manager | Tags, changelog, SBOM | Release checklist (Q8) |

## Q3. Definition of Ready / Done

**Ready**: story has acceptance criteria, linked requirement IDs, and test idea; dependencies known.

**Done**: code merged via PR; unit + integration tests added and green; lint, type-check, security scans green; coverage not lower than baseline; docs/OpenAPI updated; migration (if any) reversible and tested; acceptance criteria demonstrated; traceability matrix row updated.

## Q4. Defect classification

| Severity | Definition | Example | Fix target |
|---|---|---|---|
| S1 Critical | Data loss, security breach, unsafe advice shipped to a user | Advice says bleach for silk; IDOR exposes another user's photos | Immediately; release blocked |
| S2 Major | Core feature broken, no workaround | Analyze endpoint returns 500 for PNG | Before next release |
| S3 Minor | Feature works with workaround or cosmetic-functional issue | Wrong sort order in list | Scheduled |
| S4 Trivial | Cosmetic | Misaligned icon | Backlog |

Priority P1–P4 is set separately (business urgency). **Lifecycle**: New → Triaged → In progress → Fixed → Verified (by a test that failed before) → Closed. Every S1/S2 fix must add a regression test.

## Q5. Metrics tracked

Defect density (per KLOC), escaped defects per release, test pass rate, coverage (line/branch), mutation score for the decision engine, flaky-test rate (< 2%), MTTR, dependency freshness, and the ML metrics in the project's Test Plan (accuracy, per-slice metrics, ECE, abstention rate).

## Q6. Review checklist (every PR)

* [ ] Requirement ID referenced; tests added
* [ ] No secrets, no hard-coded paths, no `print` debugging
* [ ] Every DB query on user data is owner-scoped
* [ ] New endpoint documented in OpenAPI; input/output schemas are separate
* [ ] Errors handled with problem+json; no stack leaks
* [ ] Any new model/dataset registered with licence and hash
* [ ] Accessibility checked for UI changes (keyboard, labels, contrast)
* [ ] README/docs claims still true

## Q7. Environments

| Env | Purpose | Data |
|---|---|---|
| local | Development | Synthetic + small sample data |
| ci | Automated tests | Fixtures only |
| staging | Pre-release, ZAP scan, load test | Anonymised fixtures |
| prod/demo | Public demo | Real user data (privacy rules apply) |

## Q8. Release checklist

1. All CI gates green on `main`. 2. `make reproduce-metrics` matches README table. 3. Security: ZAP baseline + IDOR suite + dependency audit clean. 4. Accessibility audit (axe) no critical. 5. Load test meets SLO. 6. Migration dry-run on a copy of prod DB. 7. SBOM + changelog + model card updated. 8. Rollback plan tested. 9. Tag `vX.Y.Z`, release notes.

## Q9. Audits and reviews

Weekly self-review of open defects/risks; per-phase exit review against the roadmap's exit criteria; quarterly dependency and licence review; an ML "failure gallery" review after every model retrain.
