# Request Submission Service

## Purpose
Manages the government process request submission lifecycle by accepting, validating, storing, updating, and withdrawing citizen or staff submissions. The service renders submission experiences using compiled UI bundles and process definitions obtained from the definition domain, validates submitted payloads through a shared validation engine, persists request submissions and their revision history, and emits lifecycle events for downstream processing.

## Bounded Context
Request Submission

## Service Type
domain

## Internal Components
- **Request Submission API** (api): Exposes government-facing submission endpoints to start a submission, retrieve an existing submission, update draft or in-progress submission data, submit a request, withdraw a submitted request when allowed, and retrieve submission form runtime metadata required by the client. The API does not own process or UI definitions; it fetches the applicable compiled bundle reference and submission definition view through the application layer from the definition service.
- **Submission Application Service** (application): Orchestrates submission use cases by resolving the active process definition and compiled bundle reference from the definition service, invoking the shared validation engine, enforcing lifecycle rules, coordinating persistence of submissions and revisions, and triggering event publication after successful state changes.
- **Request Submission Domain Service** (domain): Implements core business rules for submission lifecycle management, including draft creation, payload update eligibility, final submission checks, withdrawal authorization rules, status transitions, and consistency of definition version association.
- **Submission Repository** (persistence): Persists and retrieves request submission aggregates, revision history, and references to external definition and bundle versions from the service-owned relational store.
- **Submission Event Publisher** (messaging): Publishes RequestSubmitted, RequestUpdated, and RequestWithdrawn events to the platform event bus after transactional persistence succeeds, using reliable delivery patterns such as an outbox.

## Data Owned
- None

## Consumed Events
- ProcessDefinitionPublished
- CompiledUiBundlePublished

## Emitted Events
- RequestSubmitted
- RequestUpdated
- RequestWithdrawn

## External Integrations
- None

## Security Controls
- None

## Observability
- None

## Open Questions
- Which exact event names does the definition service publish in the target platform for process definition and compiled UI bundle availability, and should they map directly to ProcessDefinitionPublished and CompiledUiBundlePublished or require renaming?
- Should the API explicitly support draft creation as a separate endpoint from final submission, or is submission creation always treated as an immediately persisted draft in the current government process model?
- Are there regulated retention or legal-hold requirements that require longer-term archival or immutable storage in addition to Aurora-backed revision history?

## Confidence
high