# 02. Business Requirements Document (BRD): LaundryMann 2.0

## 1. Business context
LaundryMann is a portfolio-grade, open-source consumer application. "Business value" here is: (a) a demonstrably correct and safe AI product, (b) credible evidence of engineering and ML rigor for employers/admissions, (c) a foundation that could become a real consumer app.

## 2. Business objectives

| ID | Objective | Why it matters | KPI | Target |
|---|---|---|---|---|
| BO-1 | Establish credibility | Reviewers distrust fabricated metrics (v1 README claims) | % of README claims reproducible by script | 100% |
| BO-2 | Deliver genuine user value | Product must solve a real pain | Task success in usability test (get a wash plan for a garment) | ≥ 90% of 5 testers, ≤ 90 s |
| BO-3 | Prove safety and trust | Bad advice destroys trust | Hard-constraint violations; user-reported harmful advice | 0 / 0 |
| BO-4 | Show production engineering | Differentiates from notebook projects | CI green, coverage, SBOM, threat model present | All present at v1.0 |
| BO-5 | Enable future extension | Later ideas need a clean base | Modules with stable interfaces | Perception / Decision / Storage separated |

## 3. Business requirements

| ID | Requirement | Priority | Traces to |
|---|---|---|---|
| BR-01 | The system shall analyse a garment photo and return a wash plan a layperson can follow | Must | FR-02..FR-08 |
| BR-02 | The system shall never contradict a detected care-label constraint | Must | FR-07, FR-08, NFR-S1 |
| BR-03 | The system shall communicate uncertainty and allow correction | Must | FR-05, FR-11 |
| BR-04 | The system shall help group mixed laundry into safe loads | Should | FR-09 |
| BR-05 | User data shall be protected and deletable | Must | FR-15, SEC-* |
| BR-06 | The project shall be reproducible by a third party in ≤ 15 min | Must | NFR-M1 |
| BR-07 | All reported model performance shall be measured on held-out real data | Must | Test Plan §ML |
| BR-08 | The system shall run without cloud inference fees (self-hosted) | Should | TRD §Infra |
| BR-09 | The UI shall be accessible (WCAG 2.2 AA) | Should | NFR-U1 |
| BR-10 | Commercial industrial sorting is explicitly out of scope | Must (constraint) | PD §5 |

## 4. Business rules

| ID | Rule |
|---|---|
| BRL-1 | A care-label instruction is a **hard constraint** and overrides any model output. |
| BRL-2 | If model confidence is below the abstention threshold, the system asks for a better photo or user input; it does not guess. |
| BRL-3 | Bleach/chlorine advice is never produced for silk, wool, or unknown fabrics. |
| BRL-4 | Hot water is never advised for suspected protein stains (blood, egg, milk) or when the label caps temperature lower. |
| BRL-5 | Any item flagged "dry-clean only" is excluded from home load grouping. |
| BRL-6 | User corrections are used for model improvement only with explicit opt-in and after human review. |

## 5. Stakeholder analysis and needs

| Stakeholder | Need | Requirement |
|---|---|---|
| Household user | Fast, clear instruction | BR-01, BR-09 |
| Privacy-conscious user | Photos not leaked or reused | BR-05, BRL-6 |
| Reviewer/employer | Evidence, honesty | BR-06, BR-07 |
| Developer | Low maintenance | BR-10, BO-5 |

## 6. Cost-benefit (student project)

| Item | Estimate | Note |
|---|---|---|
| Developer time | ~16 weeks × 12 h ≈ 190 h | See Roadmap |
| Compute for training | Free GPU tiers (Kaggle/Colab) or ≈ USD 20-50 rented GPU | Quotas change; budget contingency |
| Hosting demo | ≈ USD 5-10/month small VPS or free tier | CPU inference only |
| Data | Free public datasets + ~15 h collecting field set | Phone + a few swatches |
| Benefit | Portfolio asset, learning, optional real app | Qualitative |

## 7. Constraints
Solo capacity; public-dataset licences (non-commercial for some); no access to lab equipment; must run on commodity CPU; AGPL implications of YOLO26.

## 8. Assumptions and dependencies
Dataset sites stay online (mirror hashes recorded); Kaggle/Roboflow accounts available; browsers support `getUserMedia`; ISO 3758 symbols are rendered from your own vector drawings (do not copy the ISO document's artwork).

## 9. Compliance and legal
India DPDP Act 2023 and GDPR principles for personal data (Security Plan S9); dataset licence compliance (Dataset Plan §7); trademark caution for care-symbol usage; disclaimer that advice is guidance, not a substitute for the garment's label.

## 10. Success and acceptance
Business acceptance = all Must requirements verified in the traceability matrix (QAP) + BO-1..BO-4 KPIs met at v1.0.
