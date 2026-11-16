# 05. Functional Requirements Document (FRD): LaundryMann 2.0

Each module lists **inputs → processing → outputs → validation → errors → business rules → acceptance criteria**.

## M1. Accounts and sessions (FR-01, FR-15)
* **Inputs:** email, password (12-128 chars), display name.
* **Processing:** Argon2id hash; create user; issue access JWT + rotating refresh cookie (Security S2).
* **Outputs:** `201` user profile; tokens.
* **Validation:** email format, uniqueness (case-insensitive), password length, breached-password check optional.
* **Errors:** `409` duplicate; `422` invalid; `429` throttled; `401` generic "Invalid credentials".
* **Acceptance:** AC1 forged cookie with any username never authenticates; AC2 reused refresh token revokes the family; AC3 `DELETE /me` removes rows and files; AC4 export contains all user data.

## M2. Image intake (FR-02)
* **Inputs:** multipart image, `kind` ∈ {garment, basket, label}.
* **Processing:** size cap → Pillow verify → pixel cap → auto-orient → strip EXIF → resize long edge to 1280 → re-encode → store under UUID.
* **Outputs:** `image_id`, dimensions, blur score, exposure score.
* **Errors:** `413` too large; `415` unsupported; `422` corrupt; `400` too blurry/dark (with tip).
* **Acceptance:** decompression-bomb and polyglot fixtures rejected; stored file has no EXIF.

## M3. Garment detection and segmentation (FR-03)
* **Processing:** detector/segmenter (YOLO26-seg or equivalent) fine-tuned on DeepFashion2; NMS-free head; confidence ≥ 0.35 for single mode; basket mode returns up to 20 instances.
* **Outputs:** list of `{category, box, mask_rle, score}`.
* **Rule:** if no garment found → return `no_garment` with a "reframe" hint; never fall back to edge contours as a fake garment.
* **Acceptance:** on DeepFashion2 val subset mAP@0.5 ≥ 0.70 *(proposed)*; on field set instance recall ≥ 0.85.

## M4. Colour analysis (FR-04)
* **Processing (classical, deterministic):** erode mask 5 px to drop edges → convert pixels to CIELAB → k-means (k=3, weighted by area, ignore shadow pixels L*<10 and specular L*>95) → dominant colours → colour family by rules on (L*, C*, hue) → bleed-risk class:

| Family | Rule (proposed) | Bleed risk |
|---|---|---|
| white | L* ≥ 85 and C* ≤ 8 | receiver (must not mix with high-risk) |
| light | L* ≥ 70, C* < 25 | receiver |
| pastel | L* ≥ 65, C* 25-45 | low-medium |
| bright | C* ≥ 45 | high |
| dark | L* ≤ 35 | high (esp. new/indigo/black/red) |
| multi | ≥ 2 dominant colours each > 25% area with ΔE > 30 | high |

* **Why not a CNN:** colour is a *measurement*; a classifier trained on HSV-derived labels (v1) cannot exceed the rule that made the labels. Human-labelled `baseColour` from Fashion Product Images is used **only to validate** and tune thresholds.
* **Output:** palette (hex + area %), family, bleed class, confidence (based on palette separability).
* **Acceptance:** family accuracy ≥ 90% on validation subset; unit tests for boundary colours.

## M5. Fabric estimation (FR-05)
* **Sources in priority order:** (1) composition tag OCR (e.g. "60% cotton 40% polyester") → deterministic, confidence 0.98; (2) user selection; (3) image classifier (calibrated).
* **Classifier:** pretrained backbone fine-tuned on fabric-type/fibre images; outputs {cotton, linen, silk/satin, wool/knit, polyester/synthetic, denim, other}; temperature-scaled; **conformal set** at α = 0.1.
* **Abstention:** if set size > 2 or max prob < 0.55 → `unknown` and UI asks for label/selection.
* **Never** returns a default fabric on failure.
* **Acceptance:** ECE ≤ 0.05; selective accuracy ≥ 90% at ≥ 50% coverage; 100% of low-confidence cases produce `unknown`.

## M6. Stain detection (FR-06)
* **Processing:** single-class detector trained on FabricSpotDefect (+ own field images); tile large images (overlap) to keep small stains visible (v1 stains are mostly < 15% width per the label statistics).
* **Outputs:** boxes, score, area % of garment, position hint (collar, cuff, front…).
* **Type:** user chooses from {oil/grease, tea/coffee, food/curry (turmeric), ink/pen, blood/protein, mud/soil, rust, other}; stored as ground-truth label for later suggestion model (F12).
* **Rule:** the system never states a stain *type* it has not been given or trained for; UI text says "Stain found" until the user picks a type.
* **Acceptance:** mAP@0.5 ≥ 0.60; recall ≥ 0.70 field; false positives ≤ 0.5/image.

## M7. Care-label reading (FR-07)
* **Processing:** detect label region (or user crops) → OCR → normalise (fibre %, "machine wash cold", "dry clean only", etc., multilingual tokens table) → symbol detector for ISO 3758 five families (wash tub with temp dots/bars, bleach triangle, tumble dry square-circle, iron, professional-care circle).
* **Output (structured):** `{max_wash_temp_c, wash_agitation: normal|gentle|hand_only|do_not_wash, bleach: any|non_chlorine|none, tumble: normal|low|none, iron_max: 110|150|200|none, dry_clean_only: bool, fibre_composition: [...]}` with per-field confidence and source (`ocr|symbol|user`).
* **Rule:** conflicts between OCR and symbols → stricter wins and a note is shown.
* **Acceptance:** per-symbol accuracy per PD §7; strictness-on-conflict unit tests.

## M8. Decision engine (FR-08)
* **Input:** `ItemState` (colour, fabric dist, stains, constraints, garment category).
* **Processing:** (1) build constraint set from care label; (2) apply **hard** rules (BRL-1..5) as an upper bound; (3) evaluate **soft** rules from a versioned YAML rule set to choose the best action *inside* the safe set; (4) attach reasons (rule id, evidence, confidence) and warnings.
* **Output:** plan `{mode, temp_c, detergent_class, pre_treat_steps[], spin, bleach, drying, ironing, reasons[], warnings[]}`.
* **Never-do list (examples):** no chlorine bleach on silk/wool/unknown/coloured; no > 30 °C when protein stain suspected; no tumble-dry when label forbids; no mixing advice for `dry_clean_only`.
* **Acceptance:** 10k-case property test with 0 violations; every plan has ≥ 1 reason; golden tests for 50 curated scenarios reviewed by a person with domain knowledge.

## M9. Load planner (FR-09)
* Build a **conflict graph**: nodes = items; edge if incompatible (bleed-risk pair, temperature ranges do not overlap, agitation mismatch, `dry_clean_only`, heavy-soil with delicate). Colour the graph (DSATUR greedy) → minimum-ish loads; then merge loads if intersection of allowed parameters is non-empty and load size ≤ capacity input.
* **Output:** loads with items, shared parameters, and "why these are together / apart".
* **Acceptance:** no load contains a conflicting pair (property test); deterministic for same input.

## M10. Wardrobe and feedback (FR-10, FR-11)
* CRUD with owner scoping; pagination; soft delete; each analysis can be saved.
* Corrections: `PATCH /analyses/{id}/corrections` with attribute, old, new; stored with model version; `share_for_training` flag default false.
* **Acceptance:** IDOR tests pass; corrections appear in next view of item.

## M11. Export, history, admin (FR-12..14)
* PDF: server-rendered from plan JSON; contains reasons and disclaimers. History: counts and trends from DB only. Admin: scope `admin`; model activation verifies SHA-256.

## Global error and message rules
Errors use `application/problem+json` with `type`, `title`, `status`, `detail`, `instance`, `request_id`. User-facing text is plain language; internal codes are for logs.
