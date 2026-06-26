# MILESTONE 5: FINAL PRODUCT AND BETA READINESS

## GOAL

Move ANDI from prototype toward a controlled beta-ready product by finalizing the core data structure, separating each user's data, deploying the agreed version-one environment, adding monitoring, documenting deletion behavior, preparing user-facing guidance, and validating the minimum beta workflow.

## OWNERSHIP

* **Primary owner:** Soham Kinhikar
* **Supporting owners:** Jayraj Joshi and Bhuvnesh Verma

## SCOPE AND PLANNING

* **Estimated duration:** 3–6 weeks, depending on hosting decisions, product-surface decision, access stability, and model-cost findings from Milestone 4.
* **Dependencies:** Milestones 1–4 complete or materially stable, validated cost model, hosting decision, agreed user-facing surface, and approval to use real user data for beta testing.
* **Client or user validation required:** Yes. A client or approved beta user should be able to review the minimum ANDI workflow and confirm whether the outputs are useful enough for the agreed version-one beta.

## SCOPE NOTES

Milestone 5 is focused on making the agreed ANDI version-one workflow usable in a controlled beta setting. It does not promise a full-scale SaaS rollout, a polished consumer-grade application, autonomous outreach, or additional integrations beyond the approved version-one data sources. The main objective is to make the existing ANDI workflow reliable enough to demonstrate value, collect feedback, and identify what should be improved after v1.

The user-facing surface may be a lightweight web interface, internal dashboard, or integration-style surface, depending on what is approved before this milestone begins. The acceptance standard is beta usability, not full-scale commercial launch readiness.

## DELIVERABLES

* Finalized beta data structure and query cleanup for the agreed version-one entities: users, contacts, messages, calendar events, LinkedIn-derived records, retrieval records, relationship scores, briefs, dossiers, drafts, and activity records.
* Per-user data separation for contacts, source records, generated outputs, preferences, and account configuration.
* Controlled hosted beta environment with credentials stored outside the codebase and a documented deployment path.
* Monitoring view or reporting output covering cost per user, token usage, cost per workflow, latency, error rate, ingestion status, and model-call issues.
* Data deletion and account-disconnect flow with documented behavior and tested verification steps.
* Internal operations runbook for common support and recovery scenarios.
* User-facing onboarding guide explaining setup, supported data sources, known limitations, review-before-send behavior, and feedback process.
* Minimum user-facing product surface for reviewing contact ranking, morning brief or equivalent summary, dossier output, and draft/recommendation output.
* Beta-readiness report summarizing what shipped, what was tested, known limitations, cost profile, unresolved risks, and recommended next steps.

## TASKS

### Task 5.1: Finalize beta data structure and clean up product queries

* Review the records created during prototype development and identify temporary names, unused fields, duplicated records, and inconsistent query paths.
* Finalize naming and storage conventions for users, contacts, messages, calendar events, LinkedIn-derived records, retrieval records, scores, briefs, dossiers, drafts, memory records, and activity records.
* Update the application queries used for ingestion, scoring, dossier generation, draft generation, deletion, and reporting so they use the finalized beta data structure.
* Test the finalized data structure from a clean setup and from a staging/prototype copy where feasible.
* Document any temporary fields or workarounds that remain, including the owner and reason for keeping them.

### Task 5.2: Implement per-user data separation and configuration

* Ensure each user's contacts, messages, calendar events, LinkedIn-derived records, retrieval records, scores, briefs, dossiers, drafts, and preferences remain separated.
* Add checks so one user's generated outputs cannot accidentally use another user's source data.
* Test the case where two users share the same contact name, contact email, company, or meeting attendee without merging private relationship history.
* Store per-user settings for account access, timezone, brief preferences, writing style, and enabled features where required for v1.
* Document the expected behavior for single-user testing, internal testing, and approved beta-user testing.

### Task 5.3: Deploy the controlled beta environment

* Confirm the hosting decision and required services for the application, database, retrieval storage, background jobs, and model calls.
* Configure the beta environment so it can run outside a developer laptop.
* Store credentials, account-access values, model-service keys, and private configuration outside the codebase.
* Add basic health checks or documented manual checks for the application, database, retrieval storage, ingestion jobs, and model service connectivity.
* Document the deployment steps, rollback steps, and required environment variables for the team.

### Task 5.4: Add monitoring and cost visibility

* Track cost per user, cost per brief, cost per dossier, cost per draft, and token usage by workflow.
* Track latency for ingestion, retrieval, scoring, dossier generation, brief generation, and draft generation.
* Track common failure categories such as ingestion failures, account-access failures, model-call failures, retrieval failures, and output-format failures.
* Create a simple dashboard, report, or exported log summary that the team can review during beta.
* Define who reviews beta health metrics and how often they should be reviewed during the beta period.

### Task 5.5: Implement data deletion and account-disconnect behavior

* Define what user data should be deleted or disconnected, including account credentials, contacts, messages, calendar events, LinkedIn-derived records, retrieval records, scores, briefs, dossiers, drafts, memory records, files, and generated artifacts where technically feasible.
* Implement a deletion or disconnect flow appropriate for the beta product.
* Add a verification step confirming that user-owned records are removed or disconnected according to the documented behavior.
* Document any limitations, such as non-sensitive aggregate cost records that may remain for operational accounting.
* Test that deleting or disconnecting one user does not remove or alter another user's data.

### Task 5.6: Prepare internal operations runbook

* Document what to do when Gmail ingestion fails, Calendar ingestion fails, LinkedIn-derived import fails, model calls fail, generated output quality drops, costs spike, or latency increases.
* Document the steps for refreshing account access, rerunning ingestion, reviewing logs, disabling a failing workflow, and escalating unresolved issues.
* Document known limitations and expected beta failure modes so the team can respond consistently.

### Task 5.7: Prepare user-facing documentation and onboarding flow

* Write a short onboarding guide explaining supported data sources, setup steps, what ANDI generates, what it does not do, and how to provide feedback.
* Explain that generated drafts and recommendations require user review and approval before any outreach is sent.
* Document known limitations for version one, including data-source limitations, model-output limitations, and expected beta rough edges.
* Create a feedback form, notes template, or review workflow for beta users to mark useful outputs, false positives, missing context, and confusing recommendations.

### Task 5.8: Build or finalize the minimum user-facing surface

* Confirm whether the beta surface is a lightweight web interface, internal dashboard, or integration-style surface.
* Ensure a non-technical beta user can review the minimum flow without developer assistance once account access is configured.
* Provide access to contact ranking, morning brief or equivalent summary, dossier view, and draft/recommendation review.
* Include source references or explanation notes where possible so users can understand why ANDI produced an output.
* Make feedback capture available from the surface or through a clearly documented companion process.

### Task 5.9: Run controlled beta validation

* Onboard approved beta user(s) only after access, privacy, and monitoring checks are complete.
* Run the minimum beta workflow: connect/import data, process records, generate ranking, generate brief or summary, generate dossier, review draft/recommendation, and collect feedback.
* Record useful outputs, false positives, missing context, accepted/rejected recommendations, major errors, total cost, token usage, and average latency where available.
* If external beta onboarding is deferred, complete the same validation with an internal test user and clearly state that external beta usage has not yet occurred.

## ACCEPTANCE CRITERIA

* **Beta deployment readiness:** ANDI must run in the agreed hosted beta environment, not only on a developer laptop. The team must be able to provide a deployment verification record, internal access path, or walkthrough showing the system running in the beta environment.
* **Minimum beta workflow:** A user must be able to complete or observe the core version-one flow: connect/import approved data, process contacts and relationship history, review contact ranking, review a morning brief or equivalent summary, inspect a dossier, review a draft or recommendation, and provide feedback.
* **Version-one data-source boundary:** The beta product must stay within Gmail, Calendar, and LinkedIn-derived relationship data unless an additional source is separately approved. Additional integrations are not assumed as part of this milestone.
* **Per-user data separation:** The team must provide test evidence showing that one user's contacts, source records, generated outputs, preferences, and account configuration do not appear in another user's workflow.
* **Shared-contact safety:** If two users have the same contact or organization in their data, ANDI must not merge private relationship history across users unless that behavior is explicitly designed and approved.
* **Cost and token visibility:** The team must be able to report cost per user, cost per brief, cost per dossier, cost per draft, and token usage by workflow for the beta environment.
* **Reliability visibility:** The team must be able to review latency, error rate, ingestion status, account-access issues, retrieval issues, and model-call failures through a dashboard, report, or exported log summary.
* **Deletion behavior:** The user-data deletion or disconnect flow must be implemented, documented, and tested. Test evidence must show what data is removed or disconnected and what, if anything, remains for operational reasons.
* **No automatic sending:** Generated emails, messages, recommendations, or outreach actions must not be sent automatically in version one. Any draft or suggested action must require explicit user review and approval before sending.
* **User documentation:** The onboarding guide must explain supported data sources, setup steps, expected outputs, review-before-send behavior, known limitations, deletion/disconnect behavior, and how to provide feedback.
* **Operations readiness:** The internal runbook must cover the most common beta support scenarios: ingestion failure, account-access failure, LinkedIn-derived import failure, model-service failure, high cost, high latency, poor output quality, and user-support escalation.
* **Beta validation evidence:** At least one approved beta user or internal test user must review meaningful ANDI output, such as a contact ranking, brief, dossier, recommendation, or draft. Merely creating an account does not count as validation.
* **Known limitations documented:** The beta-readiness report must clearly list what is working, what is still limited, what was deferred, current cost profile, unresolved risks, and recommended next steps.

## VALIDATION EVIDENCE REQUIRED

* Hosted beta deployment verification or walkthrough record.
* Final beta data-structure notes and successful clean setup test.
* Per-user data separation test output.
* Monitoring dashboard screenshot, report, or exported metrics covering cost, token usage, latency, and error categories.
* Data deletion or disconnect test log and verification output.
* Internal operations runbook.
* User-facing onboarding guide and known-limitations note.
* Minimum product-surface walkthrough or screenshots.
* Beta validation notes for approved beta users, or internal test-user notes if external beta onboarding is deferred.
* Beta-readiness report with known limitations and post-beta recommendations.

## RISK FACTORS

* No dedicated frontend developer is currently on the team. If a polished frontend is required, it should be separately scoped or the v1 surface should remain lightweight.
* Hosting and model costs are estimates until the Milestone 4 cost model is validated. Cost monitoring should be active before external beta use.
* Beta users may have trust concerns around generated relationship recommendations. Source references and explanation notes should be visible wherever possible.
* Data deletion can be difficult when data is spread across multiple storage systems and generated outputs. Test deletion before external beta onboarding.
* Model outputs may still miss context or produce low-value recommendations. Beta feedback should be used to identify which outputs need further tuning after v1.

## OUT OF SCOPE

* Additional data sources or integrations beyond Gmail, Calendar, and LinkedIn-derived relationship data unless separately approved.
* Mobile application work.
* Fully autonomous email or message sending.
* A polished consumer-grade frontend beyond what is required for beta usability.
* Advanced administration, broad compliance programs, or commercial launch requirements beyond the agreed controlled beta scope.

## FINAL COMPLETION CHECKLIST

ANDI should not be considered beta-ready until the following are true:

* Ingestion works across the agreed version-one data sources and produces usable reports.
* The beta data structure supports per-user records and has been tested from a clean setup.
* Contact Knowledge Graph exists and can be inspected.
* Scoring system is calibrated against reviewed contacts.
* Morning brief or equivalent summary produces useful, low-noise signals.
* Evaluation harness runs and stores output.
* Cost per contact, cost per brief, cost per user, and token usage are documented.
* The private integration layer is separated from private scoring, ranking, dossier-generation, and user-data logic.
* Privacy and access review is complete before any external beta use of real user data.
* Generated drafts require explicit user approval before sending.
* Dossier and draft outputs include source support where possible.
* User-facing beta workflow is usable by an approved client or internal test user.
* Data deletion or disconnect behavior is documented and tested.
* Runbook, onboarding guide, known limitations, and beta-readiness report are complete.
