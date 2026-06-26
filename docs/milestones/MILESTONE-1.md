# MILESTONE 1: DATA INGESTION, CLEANING, AND STORAGE

## GOAL

Build the first reliable data foundation for ANDI by ingesting Gmail, Calendar, and LinkedIn-derived relationship data; normalizing the records; storing them in a per-user database; and indexing content for later retrieval and reasoning.

## OWNERSHIP

* **Primary owner:** Soham Kinhikar
* **Supporting owners:** Jayraj Joshi and Bhuvnesh Verma

## SCOPE AND PLANNING

* **Estimated duration:** 1.5–3 weeks, depending on platform access, account size, and LinkedIn import method.
* **Dependencies:** Gmail account access, Calendar account access, selected database, selected retrieval-indexing and storage approach, and access to the available LinkedIn-derived data source.
* **Client or user validation required:** Yes. A test user must confirm that the ingested contacts and relationship history are directionally accurate.

## SCOPE NOTES

This milestone should prioritize reliable ingestion and data quality over advanced intelligence. The AI layer should be limited to extraction, chunking, retrieval indexing, and memory initialization needed to support later scoring and dossier generation. Multi-user architecture should begin here at the data structure level, even if only one user is active during testing.

If direct LinkedIn ingestion is blocked or unstable, version one should support LinkedIn data through CSV export, manual import, or a controlled normalization pass rather than blocking the entire product on live LinkedIn automation.

## DELIVERABLES

* Working Gmail ingestion pipeline with account access configuration, thread/message parsing, header normalization, deduplication, and ingestion logs.
* Working Calendar ingestion pipeline with event parsing, attendee extraction, timestamps, recurrence handling where feasible, and ingestion logs.
* LinkedIn normalization/import flow using the available source format, with a fallback path for CSV or export-based ingestion.
* Beta-ready per-user database structure covering users, contacts, email messages, calendar events, LinkedIn records, retrieval records, contact graph edges, scores, briefs, drafts, and activity logs.
* Contact Knowledge Graph data structure and initial graph build using tier 1, tier 2, and tier 3 relationship categories.
* Search-indexing pipeline with documented retrieval approach, chunking strategy, and storage method, and retrieval smoke tests.
* Interruption handling for large ingestion jobs.
* Daily, weekly, or manual ingestion schedule with reporting summary.
* Gmail draft tool-calling foundation that can create and update drafts without sending them automatically.

## TASKS

* Set up Gmail ingestion through the private integration layer, including account access configuration, thread retrieval, pagination, platform-limit handling, and retry behavior.
* Set up Calendar ingestion through the private integration layer, including event retrieval, attendee extraction, event metadata parsing, and recurrence handling where feasible.
* Set up LinkedIn ingestion or import path via private integration layer, CSV/export, or controlled browser automation depending on access constraints.
* Normalize email headers, sender/recipient fields, timestamps, and thread identifiers across all ingested email threads.
* Define the per-user database structure for users, contacts, messages, calendar events, LinkedIn records, retrieval records, contact graph edges, relationship scores, briefs, drafts, and activity logs.
* Build the Contact Knowledge Graph with tier 1, tier 2, and tier 3 relationship categories.
* Implement contact deduplication across Gmail, Calendar, and LinkedIn-derived records.
* Select and configure the retrieval indexing model, chunking strategy, and search storage method.
* Index normalized email, calendar, and LinkedIn-derived content and verify retrieval quality with sample queries.
* Add interruption handling so large ingestion jobs can continue safely or restart without duplicating records.
* Run LinkedIn data normalization pass to clean lead summaries, profile notes, and messages.
* Initialize the memory layer using mem0.ai or an equivalent approach for contact-level memory persistence and retrieval.
* Build ingestion cadence options for daily, weekly, monthly, and manual refresh modes.
* Build ingestion reports showing processed records, skipped records, duplicates, failures, and data-source coverage.
* Implement Gmail draft tool-calling foundation for creating and updating drafts without automatic sending.

## ACCEPTANCE CRITERIA

* Gmail history for the selected test account is ingested, deduplicated, stored, and indexed for retrieval within the agreed scope of available API permissions.
* Calendar history for the selected test account is ingested, normalized, stored, and linked to known contacts where possible.
* LinkedIn-derived data is imported and normalized using either direct ingestion or the documented fallback path.
* Contact Knowledge Graph is built from email, calendar, and LinkedIn-derived records.
* A large ingestion job can recover from an interruption or restart cleanly without duplicating records.
* Bot-filtered or irrelevant contact list is reviewed against a manually labeled sample, with a target false-positive rate below 2 percent. If the target is not reached, the remaining failure cases must be documented with a remediation plan.
* Database structure supports per-user storage for all major entities and can be recreated cleanly from data setup.
* Ingestion pipeline produces a readable summary report after each run.
* No email sending behavior exists without explicit user approval.

## VALIDATION EVIDENCE REQUIRED

* Ingestion report showing record counts by source: Gmail messages, Gmail threads, Calendar events, LinkedIn records, contacts, graph edges, and retrieval records.
* Database data-structure update files and successful clean-database data-structure update test.
* Sample retrieval test showing that context search returns relevant relationship context.
* Interruption-handling test using a simulated ingestion failure.
* Manual review sheet for bot filtering and contact deduplication.

## RISK FACTORS

* Large ingestion recovery can add complexity. If unstable, the team may use documented manual restarts temporarily and revisit after the first reliable ingestion pass.
* LinkedIn data may have format drift or access restrictions. Validate source format early and maintain a CSV/export fallback.
* Data retention policies and privacy concerns are significant because Gmail, Calendar, and relationship data are sensitive.
* Large Gmail histories may increase ingestion time and model and retrieval-indexing cost. Track cost and runtime early.

## OUT OF SCOPE

* Fully autonomous outreach.
* Polished production frontend.
* Final scoring model calibration.
* Multi-user external launch beyond data structure readiness and local/internal testing.
