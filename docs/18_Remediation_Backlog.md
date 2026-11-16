# 18. Remediation Backlog: every v1 issue → fix → proof (LaundryMann)

Severity per QAP Q4 (S1 critical … S4 trivial). "Evidence" refers to files in the uploaded v1 repo. **Phase** refers to the Roadmap. Each item is done only when its acceptance test exists and passes.

## A. Security

| ID | Sev | Issue and evidence | Root cause | Fix | Docs | Acceptance test | Phase |
|---|---|---|---|---|---|---|---|
| LM-01 | S1 | `streamlit_app.py`: auth cookie `nexus_auth` stores the plain username and is trusted on load → anyone can set the cookie and be logged in as any user | Identity stored client-side without signature | Remove cookie identity; JWT access token (memory) + rotating HttpOnly refresh cookie | 14 S2/T1, 06 | `test_forged_cookie_rejected` | P0 (quick-fix) → P1 |
| LM-02 | S1 | `src/auth.py`: unsalted SHA-256 password hashes; `.gitignore` ignores `wardrobe.db` but not `laundry_users.db` | Legacy code, incomplete ignore list | Argon2id; delete legacy auth; force password resets; ignore `*.db` | 14 S2 | `test_argon2_params`, gitleaks/`git ls-files` check | P0/P1 |
| LM-03 | S1 | `api.py` endpoints (`/analyze`, `/analyze_basket`, `/analyze_tag`, wardrobe) have no authentication | Prototype | Require Bearer on all non-public routes | 07, 14 | `test_all_routes_require_auth` (introspect OpenAPI) | P1 |
| LM-04 | S1 | `/wardrobe/add` and `/wardrobe` are not per-user (global table) | No ownership model | `owner_id` on every row; owner-scoped repositories; RLS | 09 | IDOR suite | P1 |
| LM-05 | S2 | `await file.read()` with no size/type/pixel limits, then `Image.open` | No validation layer | Streaming size cap, magic-byte check, pixel cap, re-encode | 14 S4 | Upload abuse suite | P1 |
| LM-06 | S1 | `Dockerfile.txt` CMD runs Jupyter on `0.0.0.0` with `--allow-root` | Notebook-era Dockerfile | New multi-stage non-root image running Uvicorn | 06, 14 S7 | hadolint + Trivy + compose lint | P1 |
| LM-07 | S3 | Hard-coded `f:\onedrive backup\...` in `run_server.py`; ~56 MB of weights (two identical 24 MB `best.pt`/`last.pt`, `yolov8n.pt`, CNN) committed | No config layer; no artifact policy | Env-based config; `.gitignore` + release assets / HF Hub / DVC; purge history (`git filter-repo`) | 06 §6 | CI clean-clone job; repo size check < 5 MB | P0 |
| LM-08 | S3 | `frontend/app.js` hard-codes `http://localhost:8000`; uses `innerHTML` with file name and server text | Prototype | Relative API base from config; React rendering (no innerHTML); CSP | 10, 14 S5 | Lint rule + ZAP + CSP test | P3 |

## B. Machine learning

| ID | Sev | Issue and evidence | Root cause | Fix | Docs | Acceptance test | Phase |
|---|---|---|---|---|---|---|---|
| LM-09 | S2 | Stain detector has **one class** (`labels.jpg`: 3,044 instances of "stain") but README/UI imply Coffee/Wine/Oil classification | Overclaim; dataset had no types | State "stain found (type unknown)"; user-selected type; collect labels for later model | 05 M6, 17 | UI text test; README claim check | P0/P3 |
| LM-10 | S2 | Stain training log has 6 rows though `args.yaml` planned 20 epochs; mAP50≈0.74 from a noisy small val set; CPU training | Interrupted, unvalidated run | Retrain ≥ 50 epochs on GPU with group-split originals; report on frozen test + field set | 06 §3, 15 | ML-stain metrics ≥ targets | P2a |
| LM-11 | S1 | Fabric classifier: trained on **apparel-type** images; weights not in repo; code falls back to `"Cotton (Fallback)"` (visible in your generated `care_guide.pdf`) | Wrong dataset + silent default | New classifier on fabric/fibre data; **never** return a default; `unknown` + abstention; readiness gate | 05 M5, 17 D6/D7 | `test_no_fallback_fabric`, ML-fabric metrics | P2b |
| LM-12 | S2 | Decision engine checks `fabric in ["Silk","Wool"]`, which the garment-type model cannot output | Label-space mismatch | Fabric enum defined once (`Fabric`), used by model, rules, UI | 08 §1.1 | Contract test: engine enum == model classes | P2b/P3 |
| LM-13 | S2 | Colour CNN: 32×32 input, ~155k params, labels produced by your HSV thresholds ("circular") | Self-labelling | Replace with deterministic LAB analyser on mask pixels; validate on human labels (Fashion Product Images) | 05 M4 | UT-colour-*, ML-colour ≥ target | P2a |
| LM-14 | S1 | Mixed-basket bleed warning compares to `White`/`Black`/`Navy Blue`/`Dark Red`, but classifier emits `LIGHT/DARK/COLORED` → warning can never fire (safety feature dead) | Inconsistent vocabularies | Shared `ColourFamily`/`BleedRisk` enums; `LoadPlanner` with property test | 05 M9, 08 §1.5 | `test_white_red_never_same_load` | P3 |
| LM-15 | S2 | `ClothingDetector` uses COCO YOLOv8n (no garment classes) with contour fallback at conf 0.15 | Wrong model for task | DeepFashion2-trained segmenter; return `no_garment` instead of fake crops | 05 M3 | ML-garment ≥ target; `test_no_garment_message` | P2a |
| LM-16 | S2 | No calibration or abstention; raw softmax shown as confidence | Missing capability | Temperature scaling + split conformal; confidence words in UI | 08 §1.3, 10 | ML-calib (ECE ≤ 0.05, coverage 90±3%) | P2a/P2b |
| LM-17 | S2 | E-Nose / UV are two checkboxes; docs describe multispectral sensing | Aspirational feature | Remove from UI/docs; keep only a documented adapter *interface* for future real sensors | 01 §5 | Docs claim check | P0 |
| LM-18 | S3 | Care-label OCR uses substring matching (e.g. "cold") | Naive parser | Normaliser + ISO 3758 symbol detector; stricter-wins merge | 05 M7 | UT-merge-strict; OCR field accuracy ≥ 80% | P2b |

## C. Backend and engineering

| ID | Sev | Issue and evidence | Root cause | Fix | Docs | Acceptance test | Phase |
|---|---|---|---|---|---|---|---|
| LM-19 | S2 | Models load in a background thread at startup while the server already accepts requests; missing model → `None` calls | No readiness gate | `ModelRegistry` + `/health/ready`; requests return 503 until ready | 07, 08 §4 | `IT-ready-gate` | P1 |
| LM-20 | S2 | `analyze_basket` and `analyze_tag` run synchronous inference inside `async def` (blocks event loop); only `analyze_garment` uses an executor | Inconsistent concurrency | Single `AnalysisService` with semaphore + executor; timeouts | 08 §4 | Locust: health endpoint p95 stays low under load | P1 |
| LM-21 | S3 | Decision logic as if/else with bins A-G; recipe tables duplicated in `app.py`, `streamlit_app.py`, `frontend/app.js` | No single source of truth | YAML rule set + engine; plain-language plans; one table | 08 §1.4 | Golden tests; grep check for duplicate tables | P3 |
| LM-22 | S3 | Spec inconsistency: TRD says UV or odor overrides; code overrides only on odor | Doc/code drift | Superseded by LM-17 (sensors removed) | 01 | n/a | P0 |
| LM-23 | S3 | Four UIs: Tkinter `app.py`, `src/app.py`, `streamlit_app.py`, `frontend/` | Iterations kept | One React PWA; Streamlit becomes dev-only ML dashboard | 07 §9 | Repo has one UI dir | P3 |
| LM-24 | S2 | Legacy Streamlit dashboard shows hard-coded numbers ("Total Scans 124", "Water Saved 450 Gal") | Placeholder as data | Stats from DB only or removed | 05 M11 | `test_stats_from_db` | P3 |
| LM-25 | S3 | Old pins: torch 2.0.1, torchvision 0.15.2, streamlit 1.25.0, passlib 1.7.4 + bcrypt 4.0.1 (compat hack); `ultralytics` unpinned | No lockfile discipline | `uv.lock` with hashes; Renovate; Argon2id | 06 | CI lock check; pip-audit | P1 |
| LM-26 | S2 | No tests, no CI | Prototype | Test pyramid + GitHub Actions | 15, 16 | CI green; coverage gates | P1 |
| LM-27 | S3 | No logging/metrics; errors leak as raw exceptions | Missing | structlog, Prometheus, problem+json | 08 §5, 14 S10 | `test_error_shape`, log redaction test | P1 |

## D. Data, privacy, documentation

| ID | Sev | Issue and evidence | Root cause | Fix | Docs | Acceptance test | Phase |
|---|---|---|---|---|---|---|---|
| LM-28 | S2 | No privacy features (no delete/export, no retention, EXIF kept) | Not considered | Privacy service, retention job, EXIF strip | 14 S9, 09 §5 | IT-export/delete/retention | P1/P3 |
| LM-29 | S2 | Docs overclaim: PRD ">99.5% accuracy", "99.9% uptime", TRD "<300 ms", robotic conveyor; no measurements | Aspirational text | Replace with measured, proposed targets; scope conveyor/robot out | 01, 04 | Docs claim check in CI (grep for banned phrases) | P0 |
| LM-30 | S3 | Datasets not registered; leakage-prone augmentation habits; no field data | Ad-hoc data handling | Dataset registry; group-aware splits; field set | 17 | CI leakage check | P0 |
| LM-31 | S3 | `laundary_assistant.ipynb` is not a valid notebook (script content), `New Text Document.txt`, `scratch_install.py`, `debug_api.py`, `.bat` helpers at root | Scratch files committed | Delete or move to `scripts/`; single `Makefile` | 06 §6 | Repo layout check | P0 |

## Order of attack (first 10 working days)
1. LM-01, LM-06 (security quick-fixes on v1 while it is public) → 2. LM-07 (purge weights/paths) → 3. LM-29, LM-17 (make docs truthful) → 4. LM-30 (registry + field set v0) → 5. reproduce v1 metrics as baseline → then Phase 1.

## Verification of closure
`docs/qa/remediation_status.csv` lists each ID, PR link, test id, and date closed. The release checklist (QAP Q8) requires every S1/S2 item closed.
