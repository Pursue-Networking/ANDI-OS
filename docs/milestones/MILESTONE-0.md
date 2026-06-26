# MILESTONE 0: CUSTOMER DISCOVERY AND SCOPE ALIGNMENT

## GOAL

Capture the customer discovery, planning, architecture alignment, scope definition, and pre-build preparation required to make the implementation milestones executable without overcommitting the team beyond the agreed version-one scope.

## OWNERSHIP

* **Primary owner:** Soham Kinhikar
* **Supporting owners:** Jayraj Joshi and Bhuvnesh Verma

## SCOPE AND PLANNING

* **Estimated duration:** Completed before or during the beginning of implementation; timing depends on customer availability and alignment speed.
* **Dependencies:** Customer conversations, current workflow notes, available sample data, agreed version-one priorities, and confirmation of what will not be included in the first build.
* **Client or user validation required:** Yes. The customer or internal stakeholder should confirm that the planned version-one scope reflects the intended relationship-management workflow.

## SCOPE NOTES

Milestone 0 covers discovery and planning work that informs the rest of the build. It should not be described as a production implementation milestone. Its purpose is to reduce ambiguity before engineering work proceeds, especially around the user workflow, data sources, privacy expectations, model behavior, acceptance criteria, and commercial scope. This milestone may include work already completed during customer calls, early product planning, technical architecture review, and milestone drafting.

## DELIVERABLES

* Customer discovery summary capturing the target user workflow, relationship-management pain points, expected ANDI use cases, and major version-one priorities.
* Version-one scope summary defining what ANDI is expected to do during the initial build and what is intentionally deferred.
* Technical planning notes covering selected data sources, likely ingestion strategy, model usage approach, private integration layer assumptions, and known access constraints.
* Milestone plan and acceptance criteria aligned to the agreed $21,500 total project scope.
* Initial risk register covering platform access, LinkedIn limitations, privacy/security expectations, model reliability, cost uncertainty, and beta-readiness assumptions.

## TASKS

* Conduct customer discovery conversations to understand the relationship workflow, current manual process, desired outputs, and pain points.
* Identify version-one user stories for contact intelligence, signal detection, dossier generation, draft assistance, and morning brief workflows.
* Clarify available data sources and constraints, including Gmail, Calendar, LinkedIn-derived data, writing samples, and any unavailable systems.
* Define initial boundaries for user approval, privacy, and no-autonomous-send behavior.
* Translate discovery findings into implementation milestones, deliverables, acceptance criteria, and out-of-scope boundaries.
* Confirm commercial scope allocation across Milestone 0 through Milestone 5.

## ACCEPTANCE CRITERIA

* The version-one workflow is documented clearly enough for the team to explain what ANDI will do, what data sources it will use, what outputs it will generate, and what decisions remain user-approved rather than autonomous.
* The milestone plan reflects the agreed $21,500 scope allocation, including $1,250 for Milestone 0, $6,000 split across Milestones 1–3, and the remaining $14,250 split 40% to Milestone 4 and 60% to Milestone 5.
* Major technical risks are documented before implementation begins, including Gmail/Calendar access, LinkedIn fallback requirements, per-user data handling, model cost uncertainty, and the limits of open-source model usage.
* The team has a shared understanding that ANDI may use open-source models where appropriate but is not itself an open-source product and does not include a public integration layer in version one.
* Scope boundaries are explicit enough to avoid assuming systems or integrations beyond the high-level brief: Gmail, Calendar, LinkedIn-derived data, the private integration layer, model iteration, and the agreed Milestone 5 user-facing/deployment work unless separately approved.

## VALIDATION EVIDENCE

* Discovery notes or summary document.
* Updated milestone plan with commercial allocation included.
* Written list of included and excluded version-one functionality.
* Initial risk register or equivalent planning notes.

## RISK FACTORS

* Discovery can create expectations that exceed the implementation budget. Any new feature identified during discovery should be placed in future scope unless it is explicitly added to a milestone.
* Customer needs may change after implementation begins. Material changes should trigger scope review rather than being silently absorbed into existing milestones.
* Early technical assumptions may change once real data is available. The milestone plan should allow implementation details to adjust without expanding promised outcomes.

## OUT OF SCOPE

* Production deployment, model tuning, user onboarding, or implementation work that belongs to later milestones.
* Platform availability, model behavior, or external beta readiness beyond the version-one acceptance criteria.
* Finalized UI design or implementation unless separately added to later milestone scope.
