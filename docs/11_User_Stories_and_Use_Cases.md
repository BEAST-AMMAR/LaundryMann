# 11. User Stories and Use Cases: LaundryMann 2.0

## Part A. Epics and user stories
Format: *As a … I want … so that …* + acceptance criteria (Gherkin). IDs link to SRS.

### Epic E1 Accounts and privacy
**US-01 (FR-01)** As a new user I want to register so that my wardrobe is private.
```gherkin
Given I am on the sign-up screen
When I submit a valid email and a 12+ character password
Then my account is created and I am logged in
And my password is never returned or logged
```
**US-02 (FR-01)** As a user I want to log out so that nobody else can use my session.
```gherkin
When I tap Log out
Then my refresh token family is revoked
And reusing the old refresh token returns 401
```
**US-03 (FR-15)** As a user I want to delete my account and data.
```gherkin
Given I confirm deletion by typing DELETE
Then I am signed out immediately
And all my images and records are removed within 30 days
```
**US-04 (FR-15)** As a user I want to export my data.
**US-05 (FR-11)** As a user I want control over whether my corrections train models (default off).

### Epic E2 Scan and analyse
**US-06 (FR-02)** As a user I want to take or upload a photo so that the app can analyse my garment.
```gherkin
Given a 20 MB image
When I upload it
Then I see "Image too large (max 8 MB)" and nothing is stored
```
**US-07 (FR-04)** As a user I want to know if a garment might bleed.
```gherkin
Given a photo of a red T-shirt
When analysis completes
Then colour family is "bright" and bleed risk is "high"
And the plan says wash separately
```
**US-08 (FR-05)** As a user I want the app to say "Not sure" instead of guessing the fabric.
```gherkin
Given the fabric classifier's conformal set has 3 classes
Then the fabric shows "Not sure" with options to scan the label or choose
And no default fabric is stored
```
**US-09 (FR-06)** As a user I want stains outlined so that I can treat them.
**US-10 (FR-06)** As a user I want to set the stain type so that the plan uses the right pre-treatment.
**US-11 (FR-07)** As a user I want to scan the care label so that the plan respects it.
```gherkin
Given a label with "Dry clean only"
When I scan it
Then the plan excludes home washing
And any load plan lists the item under "Dry-clean only"
```
**US-12 (FR-08)** As a user I want a plan with reasons so that I trust it.
**US-13 (FR-08)** As a user I never want advice that contradicts my care label.

### Epic E3 Basket and loads
**US-14 (FR-09)** As a user I want a pile sorted into safe loads.
```gherkin
Given a white shirt and a red towel analysed
When I plan loads
Then they are in different loads
And the explanation cites bleed risk
```
**US-15 (FR-09)** As a user I want to set my machine capacity.

### Epic E4 Wardrobe and feedback
**US-16 (FR-10)** Save analysed garments to my wardrobe.
**US-17 (FR-11)** Correct a wrong attribute in two taps.
**US-18 (FR-12)** Export a PDF wash guide.

### Epic E5 Operations (admin/dev)
**US-19 (FR-14)** As an admin I want to activate a model version only if its hash matches.
**US-20 (NFR-O1)** As a developer I want request IDs and model versions in logs to debug issues.

## Part B. Use cases

### UC-01 Analyse a single garment
| Field | Content |
|---|---|
| Actor | Registered user |
| Goal | Obtain a safe wash plan |
| Preconditions | Logged in; camera or image available; models ready (`/health/ready` = 200) |
| Trigger | User taps Scan and captures/uploads |
| Main flow | 1 Upload image → 2 System validates and sanitises → 3 Detects garment → 4 Colour, fabric, stains computed in parallel → 5 Calibration applied; abstain if needed → 6 Decision engine builds plan → 7 Result displayed with confidence and warnings → 8 User saves or corrects |
| Alternate A (no garment) | System shows "No garment found; reframe" and lets user retry |
| Alternate B (low confidence) | System shows "Not sure" panel (W6); user scans label / chooses fabric; plan recomputed |
| Alternate C (label present) | Care constraints applied before plan |
| Exceptions | Image invalid (413/415/422) → message; model unavailable (503) → "Try again later"; timeout → retry option |
| Postconditions | Analysis stored with model/rule versions; plan satisfies all hard constraints |
| Business rules | BRL-1…BRL-5 |

### UC-02 Scan care label
Actor: user. Pre: analysis exists. Flow: capture label → OCR + symbols → constraints merged (stricter wins) → plan recomputed → difference highlighted ("Temperature lowered from 40 to 30 °C because of label"). Exception: unreadable → manual entry form.

### UC-03 Plan loads for a pile
Actor: user. Pre: ≥ 2 analyses. Flow: select items → set capacity → conflict graph → loads shown with reasons. Alt: item lacks care info → flagged "check label". Post: `load_plans` saved.

### UC-04 Correct a prediction
Flow: open correction sheet → choose attribute and value → save → analysis view updates; correction stored as `quarantined`; if opt-in, flagged `share_ok`. Post: no automatic training.

### UC-05 Manage privacy
Flow: Me → Export (ZIP emailed/downloaded) / Delete (confirm, sign-out, scheduled erase). Post: audit log entry.

### UC-06 Admin activates a model
Actor: admin. Pre: new model uploaded with metrics. Flow: view model card → verify SHA-256 → activate → readiness re-check → audit event. Alt: hash mismatch → refuse and alert.

## Part C. Story map (release view)

| Journey step | R1 | R2 | R3 | R4 |
|---|---|---|---|---|
| Sign up/in | US-01,02 | | US-03,04 | |
| Capture | US-06 | | | |
| Understand | US-07 | US-08,09,10,11 | | |
| Decide | | US-12,13 | US-14,15 | |
| Remember | | | US-16,17,18 | US-05 |
| Operate | US-20 | US-19 | | |
