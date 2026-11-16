# 13. Risk Management Log: LaundryMann 2.0

**Scoring:** Likelihood L (1-5) × Impact I (1-5) = Score. ≥ 15 = High (act now), 8-14 = Medium (plan), ≤ 7 = Low (watch). Owner for all: Developer unless stated. Review weekly.

| ID | Risk | L | I | Score | Early-warning trigger | Mitigation (prevent) | Contingency (if it happens) | Status |
|---|---|---|---|---|---|---|---|---|
| R01 | Public datasets don't match real phone photos (domain shift) | 5 | 4 | 20 | Field-set accuracy > 10 pts below test | Build field set early; augment with lighting/blur; fine-tune on field-train split; report slices | Narrow supported conditions in UI ("lay flat, good light"); raise abstention | Open |
| R02 | Fake/circular metrics creep back | 3 | 5 | 15 | Metric not produced by script | `make reproduce-metrics`, frozen manifests, CI leakage check | Retract claim, publish correction | Open |
| R03 | Safety: harmful advice reaches a user | 2 | 5 | 10 | Any hard-rule test failure; user report | Hard-constraint layer, property tests, mutation tests, domain review | Feature flag off, hotfix, post-mortem | Open |
| R04 | Data leakage in splits (augmented duplicates) | 4 | 4 | 16 | Suspiciously high val accuracy (>99%) | Original-image-only splits, pHash dedup, group split | Recompute metrics and re-release | Open |
| R05 | Dataset licence restrictions (research-only, scraped sources) | 4 | 3 | 12 | Licence unclear on source page | Dataset registry, allowed-use column, model cards marked research-only | Replace dataset or restrict repo to non-commercial | Open |
| R06 | AGPL-3.0 obligations (Ultralytics) | 3 | 3 | 9 | Plan to close-source or commercialise | ADR-04, detector behind interface | Swap to RF-DETR (Apache-2.0) | Open |
| R07 | CPU latency exceeds budget | 3 | 3 | 9 | p95 > 2 s in Phase 0/2 | Quantise, smaller backbone, parallel stages, downscale | Async job with progress UI | Open |
| R08 | No/limited GPU for training | 3 | 3 | 9 | Quota exhausted | Plan training slots; transfer learning; smaller runs | Paid GPU credits (small) | Open |
| R09 | Care-label OCR unreliable on real labels | 4 | 3 | 12 | Field OCR field-level accuracy < 70% | User-assisted crop, keyword normaliser, manual entry fallback | OCR optional feature; symbols+manual | Open |
| R10 | Stain *type* labels unavailable at scale | 5 | 2 | 10 | n/a (known) | UI asks the user; store labels; defer suggestion model | Keep user-selected only | Accepted |
| R11 | Security vulnerability in dependency | 3 | 4 | 12 | pip-audit/Trivy alert | Renovate, weekly audit, pinned locks | Patch/replace; rotate secrets if exposed | Open |
| R12 | Privacy breach of user images | 2 | 5 | 10 | Anomalous access logs | Private storage, signed URLs, RLS, retention, encryption | Incident plan, notify users, revoke keys | Open |
| R13 | Scope creep (robotics, sensors, chat) | 4 | 3 | 12 | New feature not in PRD | MoSCoW freeze; "Won't" list in PD | Drop to backlog | Open |
| R14 | Solo-developer burnout / schedule slip | 4 | 3 | 12 | Two consecutive missed weekly goals | 25% buffer, cut order (Roadmap §5), small PRs | Re-plan, cut scope | Open |
| R15 | Domain knowledge errors in wash rules | 3 | 4 | 12 | Reviewer disagrees with a rule | Cite sources per rule; review by experienced person; conservative defaults | Patch rule set (versioned) | Open |
| R16 | Model drift / new fabrics or colours | 2 | 3 | 6 | Rising correction rate | Monitor correction/abstention rates; periodic retrain from *reviewed* corrections | Retrain, canary release | Open |
| R17 | Feedback poisoning | 2 | 3 | 6 | Bursts of contradictory corrections | Quarantine, rate limits, review | Reject/ban, retrain from clean set | Open |
| R18 | Care-symbol IP/copyright concerns | 2 | 2 | 4 | n/a | Draw own vector pictograms following the public standard's meaning | Replace artwork | Open |
| R19 | Dataset source disappears/changes | 2 | 3 | 6 | Link 404 | Store hashes + citation + local backup where licence allows | Use mirror/alternative | Open |
| R20 | Browser camera API differences (iOS Safari) | 3 | 2 | 6 | Failing E2E on WebKit | Test on WebKit; upload fallback | Upload-only mode | Open |

## Risk review log

| Date | Reviewer | Changes |
|---|---|---|
| (template) | | New risks, score changes, closures |

## Top-5 focus (highest scores now)
R01 (20), R04 (16), R02 (15), then R05/R09/R11/R13/R14/R15 (12 each). Phase 0 work directly reduces R01, R02, R04.
