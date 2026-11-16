# 14. Security Plan and Threat Model: LaundryMann 2.0

## Part A. Assets, actors, trust boundaries

| Asset | Sensitivity | Where |
|---|---|---|
| User credentials, tokens | High | DB (hashes), memory |
| Garment/label photos | High (personal, habits) | Object store |
| Wardrobe and history | Medium | DB |
| Model files and rules | Medium (integrity critical) | Filesystem |
| Corrections dataset | Medium | DB |

**Actors:** legitimate user; malicious user (abuse, IDOR, DoS); external attacker; malicious insider/dependency; curious admin.
**Trust boundaries:** Browser ↔ Gateway; Gateway ↔ API; API ↔ DB/Object store; API ↔ model files; build pipeline ↔ registry.

## Part B. STRIDE threat model (LaundryMann-specific)

| # | Threat | STRIDE | Component | Likelihood/Impact | Control | Test |
|---|---|---|---|---|---|---|
| T1 | Forge login cookie with victim's username (v1 flaw) | Spoofing | Auth | H/H | No identity cookies; signed JWT + rotating refresh | `test_forged_cookie_rejected` |
| T2 | Steal refresh token via XSS | Info disclosure | Web | M/H | HttpOnly cookie, strict CSP, no innerHTML | ZAP + CSP test |
| T3 | Replay stolen refresh token | Spoofing | Auth | M/H | Rotation + reuse detection | `test_refresh_reuse_revokes_family` |
| T4 | Read/modify another user's analysis (IDOR) | Elevation/Info | API | H/H | Owner-scoped repos, UUIDs, RLS | IDOR suite |
| T5 | Upload decompression bomb / polyglot | DoS/Tampering | Upload | M/M | Pixel cap, magic bytes, re-encode | Upload abuse suite |
| T6 | Inference flood exhausts CPU | DoS | Inference | H/M | Rate limit, concurrency cap, queue limit, timeouts | Locust spike |
| T7 | Malicious model file replaces real model | Tampering | ModelRegistry | L/H | ONNX only; SHA-256 verify; admin-only activation; audit | `test_model_hash_mismatch_refused` |
| T8 | Adversarial patch to force "safe" plan | Tampering | Perception | M/M | Hard constraints independent of ML; abstention; care label wins | Property tests |
| T9 | Feedback poisoning to skew retraining | Tampering | Corrections | M/M | Quarantine, review, rate limits, no auto-train | `test_corrections_quarantined` |
| T10 | Secrets leaked in git | Info disclosure | Repo | M/H | gitleaks, .env.example, rotation | CI |
| T11 | Vulnerable dependency (e.g. image libs) | Multiple | Supply chain | M/H | pip-audit, Renovate, Trivy, pinned locks | CI |
| T12 | Log leakage (tokens, emails) | Info disclosure | Logging | M/M | Redaction filter; no bodies logged | `test_logs_redact` |
| T13 | Mass assignment (set `role=admin`) | Elevation | API | M/H | `extra="forbid"`, separate In/Out schemas | Schemathesis + unit |
| T14 | Account enumeration via login/register messages | Info disclosure | Auth | M/L | Generic messages; timing-safe compare | Unit |
| T15 | Insecure PDF rendering (HTML injection in plan text) | Tampering | PDF | L/M | Escape all fields; no remote resources | Unit |
| T16 | Privacy: photo retained beyond consent | Info disclosure | Storage | M/H | Retention job, delete cascade, export/delete tests | IT-delete |
| T17 | Open Jupyter/debug service exposed (v1 Docker CMD) | Elevation | Container | H/H | Remove; non-root app image | Trivy/hadolint + compose lint |

## Part C. Controls specific to LaundryMann
1. **Safety is a security property:** the decision engine is treated as a safety-critical component: hard rules cannot be disabled by config or by any ML output; changes require tests plus reviewer sign-off.
2. **OCR text is untrusted input:** parsed by a whitelist normaliser into enumerated constraints; free text is never executed, templated, or passed to a model as instructions.
3. **PDF generation** uses an allow-listed template with escaped values and no network access.
4. **Model artifacts** loaded read-only from a mounted volume; hashes verified at start and on activation.
5. **Admin surface** disabled unless `ADMIN_ENABLED=true`, separate router, scope check, extra audit.

## Part D. v1 vulnerabilities and closure (see 18 for full list)
Forged cookie (LM-01), unsalted hashes and tracked-DB risk (LM-02), unauthenticated API (LM-03), global wardrobe (LM-04), unbounded uploads (LM-05), Jupyter CMD (LM-06), hard-coded paths/secrets hygiene (LM-07).

## Part E. Common security specification
*(Shared standard also used by FridgeASSIST.)*

## S1. Security objectives and principles

| Principle | What it means here | Why |
|---|---|---|
| Secure by default | Every endpoint requires auth unless explicitly listed as public (only `/health/live`, `/auth/*`, static assets) | The old code had zero auth on the API |
| Least privilege | DB user has no DDL rights at runtime; containers run non-root, read-only FS | Limits blast radius |
| Defense in depth | Validate at edge (size/type), at schema (Pydantic), at DB (constraints) | One missed check must not become a breach |
| Privacy by design | Images stay on your server; no third-party inference APIs; EXIF stripped; retention limits | Clothing and fridge photos reveal habits, health, religion, location |
| Fail closed | On auth/validation/model-load error, deny or abstain, never guess | A wrong "safe to eat" or "safe to bleach" is worse than "I don't know" |

## S2. Authentication and session specification

| Item | Specification | Reason |
|---|---|---|
| Password hashing | Argon2id via `argon2-cffi`; at least memory 19 MiB, time cost 2, parallelism 1 (tune upward until hashing takes ~100–250 ms on the server) | Current OWASP-recommended family; replaces unsalted SHA-256 (legacy `auth.py`) and removes the fragile `passlib`+`bcrypt` pin |
| Password policy | 12–128 chars, no composition rules, optional breached-password check (k-anonymity range API) | NIST-style guidance; length beats complexity |
| Access token | JWT, 15 min lifetime, claims `sub`, `iat`, `exp`, `jti`, `scope`; signed with a key from env (rotate via `kid`) | Short-lived so theft has limited value |
| Refresh token | Opaque random 256-bit value; only its SHA-256 stored in `refresh_tokens`; rotated on every use; reuse of an old token revokes the whole family | Detects stolen refresh tokens |
| Cookie flags | Refresh token in `HttpOnly; Secure; SameSite=Strict; Path=/auth` cookie; access token kept in memory only | Fixes the forged plain-username cookie (`nexus_auth=<username>`) which allowed account takeover |
| CSRF | Access token sent via `Authorization: Bearer`; refresh endpoint protected by SameSite=Strict plus an `Origin` check | Cookie-only auth is the CSRF risk; this removes it for data endpoints |
| Brute-force | 5 login attempts/min per (IP, username) with exponential back-off; generic error "Invalid credentials" | Prevents enumeration and credential stuffing |
| Logout | Revokes the refresh-token family server-side | Real logout, not just deleting a cookie |

## S3. Authorization

* Every query on user data is scoped by owner: `WHERE owner_id = :current_user_id` (or household membership for FridgeASSIST). Implemented once in a repository base class, never ad hoc in routes.
* Object identifiers are UUIDv4 (not sequential integers) to reduce enumeration, but **UUIDs are not authorization**: ownership is still checked.
* Automated **IDOR tests** for every resource: user B must get `404` on user A's resource for GET, PATCH, DELETE.

## S4. Upload hardening (images)

1. Enforce `Content-Length` ≤ 8 MB at the reverse proxy and again in the app (stream and abort).
2. Detect type by **magic bytes** (Pillow `Image.open` + `verify()`), allow JPEG/PNG/WebP/HEIC-converted only; ignore client `Content-Type` and client filename entirely.
3. Set `Image.MAX_IMAGE_PIXELS` (for example 40 MP) to defeat decompression bombs; reject animated formats.
4. Re-encode to a clean JPEG/WebP: this strips EXIF/GPS and any appended payloads.
5. Store under server-generated UUID names in a private bucket/dir; never serve from a public static mount; serve via short-lived signed URLs.
6. Virus scan is optional (ClamAV) but the re-encode step already removes polyglot risk for images.

## S5. API and web hardening

* **CORS**: explicit allowlist of the web origin(s); never `*` with credentials (the old FridgeASSIST did exactly that).
* **Headers**: `Content-Security-Policy` (default-src 'self'; no inline scripts), `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Permissions-Policy: camera=(self), geolocation=()`.
* **XSS**: React escapes by default; forbid `dangerouslySetInnerHTML` via lint rule; never build DOM with `innerHTML` from server data (the old `script.js` did).
* **Resource consumption**: pagination max 100; request timeout 30 s; inference concurrency cap with queue and `429`/`503` + `Retry-After`.
* **Error model**: RFC 9457 `application/problem+json`; no stack traces, no internal paths.
* **Inventory of APIs**: single versioned prefix `/api/v1`; OpenAPI is the source of truth; unused routes are deleted.

## S6. Secrets and configuration

`pydantic-settings` reads env vars; `.env.example` documents keys; real `.env` is git-ignored. `gitleaks` runs as pre-commit hook and CI job. Secrets rotated on any suspicion. No hard-coded machine paths (the old `run_server.py` had `f:\onedrive backup\...`).

## S7. Supply chain and container security

| Control | Tool | Gate |
|---|---|---|
| Lock files with hashes | `uv lock` / `pip-compile --generate-hashes`, `npm ci` | CI fails if lock drifts |
| Vulnerable dependencies | `pip-audit`, `npm audit --omit=dev` | Block on High/Critical |
| Static analysis | `bandit`, `ruff` (S rules), `semgrep` (optional) | Block on High |
| Secrets | `gitleaks` | Block on any finding |
| Container scan | `trivy image` | Block on Critical |
| SBOM | CycloneDX (`cyclonedx-py`) attached to each release | Release checklist |
| Actions pinned | Pin third-party GitHub Actions to commit SHA | Review on update |
| Image | Multi-stage, digest-pinned base, non-root user, read-only root FS, no `jupyter` CMD (the old LaundryMann Dockerfile CMD launched Jupyter on `0.0.0.0` with `--allow-root`) | Trivy + hadolint |

## S8. ML-specific security

| Threat | Control |
|---|---|
| Malicious model file (pickle RCE via `torch.load` on torch 2.1.x default) | Serve **ONNX** only; training code uses `torch.load(..., weights_only=True)` or safetensors; SHA-256 of every model file recorded in `model_versions` and verified at startup |
| Adversarial or out-of-distribution image | Calibrated confidence + conformal abstention; low-confidence path asks user for a second photo or a manual choice |
| Feedback poisoning (users submit wrong corrections) | Corrections are stored but **never auto-trained**; quarantined, rate-limited per user, reviewed before entering a training manifest |
| Data provenance / licence violation | `datasets/REGISTRY.md` records source, licence, hash, and allowed use for every dataset; CI check that training manifests only reference registered datasets |
| Model extraction / abuse | Per-user rate limits; confidence scores rounded in public responses |
| Prompt injection | Not applicable in the MVP (no LLM reads OCR text). If an LLM is added later, OCR text is treated as untrusted data, never as instructions |

## S9. Privacy and legal

* **Data minimization**: store only what a feature needs; drop EXIF; no precise location.
* **Retention**: images kept 90 days by default (user-configurable, 7–365); derived records kept until deleted.
* **User rights**: `GET /me/export` (JSON + images zip) and `DELETE /me` (hard delete within 30 days, immediate soft-lock) implemented as first-class features.
* **Encryption**: TLS 1.2+ in transit; disk/bucket encryption at rest.
* **Regulation**: design follows GDPR principles and India's Digital Personal Data Protection Act, 2023 (consent, purpose limitation, erasure). This is engineering guidance, not legal advice; get a lawyer before any public launch that collects other people's data.
* **Consent**: explicit opt-in (default off) before user corrections may be used to improve models.

## S10. Logging, monitoring, audit

Structured JSON logs (`structlog`) with `request_id`, `user_id` (hashed), route, status, latency, model version. Never log passwords, tokens, image bytes, or full emails. Audit events: login success/failure, token reuse, password change, data export, delete-account, admin actions, model activation. Alerts (email/Telegram) on: 5xx rate, auth-failure spike, refresh-token reuse, model hash mismatch.

## S11. Incident response (lightweight)

1. Detect (alert or report) → 2. Contain (revoke tokens, disable feature flag) → 3. Eradicate (patch, rotate secrets) → 4. Recover (deploy, verify) → 5. Post-mortem within 5 working days (blameless, recorded in `docs/incidents/`). Severity follows the defect scale in the QAP.

## S12. Standards mapping

**OWASP API Security Top 10 (2023)**

| ID | Risk | Mitigation in this design |
|---|---|---|
| API1 | Broken object-level authorization | S3 owner scoping + IDOR tests |
| API2 | Broken authentication | S2 |
| API3 | Broken object property-level authorization | Separate Pydantic *input* and *output* schemas; `extra="forbid"`; no mass assignment |
| API4 | Unrestricted resource consumption | S5 limits, upload caps, inference concurrency cap |
| API5 | Broken function-level authorization | Role scopes (`user`, `admin`); admin routes in separate router with scope check |
| API6 | Unrestricted access to sensitive business flows | Rate limit registration, feedback, export |
| API7 | SSRF | No server-side URL fetching from user input |
| API8 | Security misconfiguration | S5, S7, secure defaults, config validation at startup |
| API9 | Improper inventory management | Single `/api/v1`, OpenAPI diff check in CI |
| API10 | Unsafe consumption of APIs | Only fixed, allow-listed outbound calls (push/email); timeouts and TLS verify |

**OWASP ASVS**: target **Level 1 fully, Level 2 for V2 (authentication), V3 (session), V4 (access control), V5 (validation), V8 (data protection)**.

## S13. Generic security test matrix

| Test | Tool | Frequency |
|---|---|---|
| SAST | bandit, ruff-S, semgrep | Every PR |
| Dependency audit | pip-audit, npm audit | Every PR + weekly |
| Secrets scan | gitleaks | Every PR |
| DAST baseline | OWASP ZAP baseline scan against staging | Every release |
| API fuzz / contract | schemathesis (from OpenAPI) | Every PR (short), nightly (long) |
| AuthZ / IDOR suite | pytest | Every PR |
| JWT tamper tests (alg=none, expired, wrong kid, replay) | pytest | Every PR |
| Upload abuse (bomb, polyglot, wrong magic, oversized) | pytest with fixtures | Every PR |
| Container scan | trivy | Every build |
| Manual pen-test checklist | ASVS L1 checklist | Before v1.0 |
