# LaundryMann 2.0: Documentation Pack

**Version:** 1.0  |  **Date:** 19 Sep 2026  |  **Status:** Draft for owner review  |  **Scope:** Fix the existing project (v1) into a correct, secure, testable v2. The "unique flagship idea" (Part 5 of the earlier discussion) is intentionally **out of scope** here and will be handled later; extension points are noted but not built.

## How to read this pack

| # | Document | Question it answers | Read it when |
|---|---|---|---|
| 01 | Project Document (PD) | What are we building, why, and what is the baseline? | First |
| 02 | Business Requirements (BRD) | What value/goals justify the work? | Prioritising |
| 03 | Product Requirements (PRD) | Who is it for and which features? | Planning releases |
| 04 | Software Requirements Specification (SRS) | Precisely what must the software do (testable)? | Writing tests |
| 05 | Functional Requirements (FRD) | Module-by-module behaviour, rules, acceptance | Implementing |
| 06 | Technical Requirements (TRD) | Stack, models, budgets, environments | Setting up |
| 07 | Software Architecture (SAD) | How is it structured and why? | Designing |
| 08 | Technical Design (TDD) | Module/algorithm/API design, plus the test-driven-development plan | Coding |
| 09 | Database and ER | Tables, relations, constraints | Migrations |
| 10 | UI/UX and Wireframes | Screens, flows, design system | Front-end |
| 11 | User Stories and Use Cases | Behaviour from the user's side | Acceptance |
| 12 | Roadmap | What, when, exit criteria | Scheduling |
| 13 | Risk Register | What can go wrong, what we do | Weekly review |
| 14 | Security Plan | Threat model and controls | Every PR |
| 15 | Test Plan | How we test, incl. ML evaluation | CI and QA |
| 16 | Quality Assurance Plan (QAP) | Process, roles, defects, release | Governance |
| 17 | Dataset Plan | Which datasets, exact links, why, how used | Phase 0-2 |
| 18 | Remediation Backlog | Every issue found in v1 → fix → test | Daily |
| - | `schema.sql`, `openapi.yaml` | Machine-readable DB schema and API contract | Coding |

**Acronym note (TDD):** the request listed "TDD". In this pack it is used as **Technical Design Document**; document 08 *also* contains the **Test-Driven Development** plan so both meanings are covered.

## Ground rules used throughout

1. **Every claim is measurable.** Targets marked *(proposed)* must be re-baselined in Phase 0 and then frozen.
2. **Requirement IDs** (`BR-`, `FR-`, `NFR-`, `SEC-`) are stable and appear in tests for traceability.
3. **v1 facts** cited here come from a static audit of the uploaded repository (code read, not executed).
4. **Dataset facts** (sizes, links) were checked against the source pages on 19 Sep 2026; licences must be re-verified by you before use (Dataset Plan §7).
