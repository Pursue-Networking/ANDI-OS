# MILESTONE 2: SCORING AND NOISE MODEL

## GOAL

Convert ingested relationship data into usable signal by ranking contacts, identifying meaningful relationship events, filtering noise, and producing an accurate morning brief.

## OWNERSHIP

* **Primary owner:** Soham Kinhikar
* **Supporting owners:** Jayraj Joshi and Bhuvnesh Verma

## SCOPE AND PLANNING

* **Estimated duration:** 2–3 weeks after Milestone 1 is complete.
* **Dependencies:** Completed ingestion pipeline, stable Contact Knowledge Graph, labeled sample contacts, enough Gmail/Calendar/LinkedIn-derived data for evaluation, and initial cost tracking from ingestion.
* **Client or user validation required:** Yes. The primary user must review contact rankings, false positives, and the morning brief quality.

## DELIVERABLES

* Network scoring system using Gmail, LinkedIn-derived data, Calendar activity, and ANDI-specific subscores.
* Signal taxonomy defining what counts as a useful signal, weak signal, duplicate signal, irrelevant signal, and false positive.
* Triage rules covering promote, skip, and hold decisions.
* Four-layer evaluation harness covering extraction accuracy, scoring precision, triage recall, and brief relevance.
* Ranked morning brief generator with signal explanations and references back to source records where possible.
* Calibration report using at least 100 labeled contacts and top-50 contact review.
* Cost-per-contact and cost-per-brief measurement report.

## TASKS

* Define scoring inputs and subscores from Gmail, Calendar, LinkedIn-derived data, and ANDI-specific activity.
* Implement network scoring using recency, frequency, relationship strength, explicit user importance, response patterns, meeting history, and relevant keywords.
* Build triage system with 7 envelope rules covering promote, skip, and hold behavior.
* Define signal taxonomy for calendar events, Gmail threads, LinkedIn-derived updates, keywords, and relationship-change events.
* Build signal detection for calendar events, Gmail threads, relationship keywords, meeting cadence changes, unanswered messages, and upcoming follow-up opportunities.
* Build scoring system to prioritize signals by urgency, relationship value, source confidence, freshness, and actionability.
* Implement phase 3 triage pipeline connecting classifier, routing, and brief-generation logic.
* Run triage rule iteration against real data from Milestone 1.
* Build 4-layer eval harness covering extraction accuracy, scoring precision, triage recall, and brief relevance.
* Implement adaptive tier boundaries that adjust when contact volume changes by more than 20 percent.
* Refine signal scoring to produce a ranked morning brief.
* Calibrate network scores by reviewing the top 50 contacts and spot-checking low-ranked contacts.
* Implement cost-per-contact and cost-per-brief measurement using model usage and model call tracking.
* Collect ground-truth labels from at least 100 contacts for calibration.
* Document scoring formula, weighting assumptions, and known limitations.

## ACCEPTANCE CRITERIA

* Triage rules are evaluated against a 100-contact manual label set, with a target agreement rate above 90 percent. If the target is not reached, the milestone can close only with documented failure categories, examples, and next-step tuning recommendations.
* Top-20 network-score ranking is reviewed against expected relationship strength, with a target of at least 80 percent reviewer agreement. Material mismatches must be documented with likely causes such as missing data, stale data, weighting error, or ambiguous relationship history.
* Morning brief is evaluated during a defined test window, with a target of fewer than 3 false-positive signals per day. If the target is missed, false positives must be categorized by source and triage rule before launch use.
* Four-layer eval harness runs on every build or evaluation run and produces saved output.
* Cost per contact and cost per brief are measured, documented, and associated with model/tool usage.
* Tier-boundary adjustment logic is tested against at least two contact-volume scenarios, including a greater-than-20-percent volume change. The output should preserve a reasonable tier distribution, or the exceptions must be documented before use.
* Every promoted signal includes a short explanation of why it was promoted.

## VALIDATION EVIDENCE REQUIRED

* 100-contact labeled calibration set with promote, skip, hold, or tier labels.
* Top-50 contact review sheet showing expected versus actual ranking.
* Evaluation harness output for extraction accuracy, scoring precision, triage recall, and brief relevance.
* Sample morning briefs with false positives marked.
* Cost report showing cost per contact, cost per brief, and most expensive operations.

## RISK FACTORS

* Scoring calibration is meaningless without full-enough data from Milestone 1. This milestone should not begin until ingestion quality is acceptable.
* Cost per contact may exceed what is viable for the unit economics. Identify the most expensive operations early and plan optimization in Milestone 4.
* Adaptive tier boundaries trained on a single user may overfit. Validate logic against at least two distinct contact volumes before finalizing.
* A model can appear accurate while still missing high-value relationship context. Manual user review is required.

## OUT OF SCOPE

* Final polished UI.
* Fully polished dossier generation.
* Voice-matched email drafting beyond basic signal-to-draft experimentation.
* External multi-user launch.
