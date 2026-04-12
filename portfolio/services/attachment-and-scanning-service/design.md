# Attachment and Scanning Service

## Purpose
Issues presigned upload URLs for attachments associated with a submission, tracks submission-level attachment scanning progress, dispatches scan requests to the scanning system, processes scan outcomes, and emits workflow events when attachments are clean or infected.

## Bounded Context
Attachment Intake and Scan Orchestration

## Service Type
domain

## Internal Components
- **Attachment API** (api): Provides endpoints to register attachment uploads, generate presigned upload URLs, retrieve attachment and submission scan status, and support authorized internal operations.
- **Attachment Workflow Application Service** (application): Coordinates attachment registration, upload URL issuance, scan dispatch initiation, processing of scan result events, and evaluation of whether a submission is ready for civil servant review.
- **Attachment Scanning Domain Logic** (domain): Enforces lifecycle rules for attachment scan orchestration, validates allowed status transitions, ensures idempotent handling of scan outcomes, and determines when to emit completion or failure workflow events.
- **Attachment Persistence Adapter** (persistence): Persists owned scan job, dispatch, and submission attachment status data with transactional consistency for workflow progression and event processing.
- **Attachment Messaging Adapter** (messaging): Consumes request submission and scan result events, publishes baseline attachment scanning events, and supports reliable delivery, retries, correlation, and idempotent processing.

## Data Owned
- None

## Consumed Events
- RequestSubmitted
- FileScannedClean
- FileScannedInfected

## Emitted Events
- ScanRequested
- RequestReadyForCivilServantReview
- AttachmentScanCompleted
- AttachmentScanFailedOrInfected

## External Integrations
- None

## Security Controls
- Authenticated and authorized access to API operations using platform identity controls and service-to-service authorization.
- Presigned upload URLs are short-lived, scoped to a specific attachment upload, and constrained to approved object key patterns and content rules where supported.
- Encryption in transit for APIs, event transport, and integrations; encryption at rest for relational data and object storage.
- Audit logging for attachment registration, presigned URL issuance, scan dispatch, scan result processing, and workflow event emission.
- Least-privilege access to object storage, database, and messaging resources.
- Input validation and correlation checks on scan result events to prevent unauthorized or malformed state transitions.

## Observability
- Structured logs for API requests, upload URL issuance, scan dispatch attempts, consumed scan result events, and emitted workflow events.
- Metrics for attachment registrations, presigned URL generation success/failure, scan dispatch latency, scan completion rates, infected file rates, retry counts, and time-to-review-readiness per submission.
- Distributed tracing across API handling, persistence operations, message publishing/consumption, object storage interactions, and scanning system integration.
- Operational alerts for scan result processing failures, dispatch backlogs, repeated retry exhaustion, and abnormal infection or failure rates.

## Open Questions
- None

## Confidence
high