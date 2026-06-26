# MILESTONE 3: PRIVATE INTEGRATION LAYER

## GOAL

Build a private integration layer that supports ANDI's internal tool calls, Gmail and Calendar connectors, authentication, documentation, and test coverage. This milestone does not include publishing a public integration layer or open-sourcing ANDI product code.

## OWNERSHIP

* **Primary owner:** Soham Kinhikar
* **Supporting owners:** Jayraj Joshi and Bhuvnesh Verma

## SCOPE AND PLANNING

* **Estimated duration:** 1.5–2.5 weeks, partially parallelizable with Milestone 2 after the internal interface design is stable.
* **Dependencies:** Stable internal ingestion interfaces, authentication decision, test accounts, packaging decision, private repository access, and security review checklist.
* **Client or user validation required:** No for initial internal build. User validation is only required if the integration layer affects visible Gmail, Calendar, draft, or brief behavior.

## SCOPE NOTES

The integration layer should expose a clean private interface for the ANDI application to call supported tools and data sources. It may follow standard integration-layer patterns, but it is not intended to be a public integration layer, public package, or open-source repository. The product may use open-source models in selected model workflows, but the ANDI application, scoring logic, relationship intelligence, private data structures, and internal orchestration code remain private. This milestone should avoid overbuilding a developer platform. The goal is reliable internal integration, testable tool calls, secure credentials, and maintainable boundaries between ingestion, scoring, model generation, and user-facing workflows.

## DELIVERABLES

* Private integration-layer specification covering internal tool names, request format, response format, error format, retry behavior, and change-management notes.
* Private repository or internal package with documented setup for the ANDI team.
* Gmail connector callable through the internal integration layer after documented account access configuration.
* Calendar connector callable through the internal integration layer after documented account access configuration.
* Internal authentication layer using private keys, service credentials, or another agreed mechanism suitable for the private beta environment.
* Internal README, setup guide, internal tool reference, and example environment file.
* Integration test suite covering connector calls, error paths, authentication failures, and parity with the internal ingestion endpoints where applicable.
* Documented test workflow for linting, formatting, unit tests, and integration tests in the private repository.
* Security review checklist completed before using the integration layer with real user data.

## TASKS

* Define the internal integration-layer tool interface, including naming conventions, required inputs, optional inputs, output format, error format, timeout behavior, and retry rules.
* Document which tool calls are required for version one: Gmail ingestion, Calendar ingestion, contact lookup, draft creation/update, retrieval, and status reporting.
* Define the boundary between the integration layer and private ANDI product logic so scoring, ranking, dossier generation, voice profiles, and user data remain inside the private application layer.
* Decide the private repository structure, package/module layout, runtime environment, dependency management approach, and release process for internal use.
* Build the authentication layer with API-key, internal credential, or internal secret-based access control.
* Add Gmail connector support for configured accounts, including pagination, platform-limit handling, thread/message retrieval, attachment metadata where needed, and safe failure behavior.
* Add Calendar connector support for configured accounts, including event retrieval, attendee extraction, recurrence handling where feasible, and safe failure behavior.
* Add configuration templates documenting required environment variables, account access credentials, model service credentials where relevant, and local/staging separation.
* Write internal documentation: README, setup guide, tool reference, example calls, common errors, and troubleshooting notes.
* Write integration tests for successful tool calls, invalid credentials, missing configuration, platform-limit responses, empty accounts, malformed records, and partial failures.
* Set up a documented test command that runs formatting checks, unit tests, and integration tests before changes are merged.
* Conduct security review before using real user data to check for leaked credentials, internal URLs, private data structures, sensitive user data, and unsafe logging.
* Confirm that no public release, public package, public repository, or external developer-support obligation is included in version one.

## ACCEPTANCE CRITERIA

* **Private interface readiness:** The internal integration-layer interface is documented well enough for an ANDI developer to add or call a supported tool without reading unrelated product code. The documentation must include tool names, inputs, outputs, error codes, expected retries, and authentication requirements.
* **No public/open-source product claim:** The milestone documentation, repository metadata, README, and release notes must not describe ANDI as an open-source product or describe this work as a public integration layer. Any reference to open source must be limited to open-source models or libraries used as dependencies.
* **Connector functionality:** Gmail and Calendar connectors must successfully run in a configured development or staging environment using approved test credentials. The test output must show at least one successful Gmail retrieval path and one successful Calendar retrieval path, unless a connector is blocked by third-party access limits that are documented as a dependency issue.
* **Authentication coverage:** Internal authentication must be present, documented, and tested for success and failure cases. Invalid or missing credentials must fail safely without exposing credentials or sensitive user data.
* **Configuration clarity:** Required environment variables, account access credentials, local/staging separation, and setup steps must be documented. A developer with the correct private credentials should be able to configure the integration layer without guessing hidden setup steps.
* **Test coverage:** Integration tests must cover successful connector calls, invalid credentials, missing configuration, empty results, malformed records, and partial failures. Any tests that require live credentials must be clearly marked and separated from offline tests.
* **Security review:** Before the integration layer is used with real user data, the security checklist must confirm that credentials are not committed, logs do not expose sensitive raw content by default, internal URLs are not unnecessarily exposed, and user data is not included in fixtures or documentation.
* **Private boundary:** No private ANDI scoring logic, relationship-ranking logic, dossier-generation logic, voice-profile data, user data, credentials, or internal product strategy is exposed outside the private repository or internal deployment boundary.
* **Scope control:** There is no requirement in this milestone to publish a public package, support third-party developers, maintain a public repository, or provide a hosted external integration-layer service.

## VALIDATION EVIDENCE REQUIRED

* Internal interface specification or tool-reference document.
* Private setup guide and example configuration file with credentials redacted.
* Test output showing Gmail and Calendar connector calls in development or staging.
* Authentication success/failure test output.
* Integration test report or local test log.
* Security review checklist confirming no committed credentials, no unsafe logging, and no public/open-source release claims.
* Boundary review note confirming that scoring, ranking, dossier generation, voice profile, and user data remain private.

## RISK FACTORS

* Expanding the integration layer beyond the private ANDI workflow would create unnecessary scope and maintenance burden. Keep the version-one layer private and narrow.
* Gmail and Calendar behavior may vary by account permissions, account access permission approval, platform limits, and account size. Failures should be documented rather than treated as guaranteed platform support.
* Security issues are easy to introduce when working with account access credentials and user data. Review logging, fixtures, screenshots, and config files before real user testing.
* Internal interface changes can break ingestion, scoring, or draft workflows. Version the interface and maintain integration tests before changing request or response data structures.

## OUT OF SCOPE

* Public integration release.
* Open-sourcing ANDI product code, scoring logic, ranking logic, dossier-generation logic, or internal orchestration code.
* Public repository, public package distribution, public release process, or external developer-support process.
* Supporting data sources beyond Gmail, Calendar, and LinkedIn-derived data unless separately approved.
* A full hosted SaaS deployment of the integration layer as a standalone product.
