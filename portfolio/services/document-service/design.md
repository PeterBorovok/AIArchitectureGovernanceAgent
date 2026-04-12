# Document Service

## Purpose
Manages platform documents and their versions, including document metadata, lifecycle state, version history, links to business artifacts such as submissions, and long-term storage of document binaries for attachments, knowledge documents, policy documentation, and committee decisions.

## Bounded Context
Document Management

## Service Type
domain

## Internal Components
- **Document API** (api): Exposes synchronous endpoints for registering documents, uploading or registering new document versions, updating metadata, linking documents to submissions, publishing, archiving, blocking, and retrieving document details and version history.
- **Document Application Service** (application): Coordinates document use cases, validates commands, orchestrates lifecycle transitions, enforces preconditions such as scan status and publication rules, persists metadata, coordinates binary storage interactions, and publishes resulting domain events.
- **Document Domain Engine** (domain): Implements business rules for document identity, version sequencing, metadata governance, lifecycle state transitions, publish and archive eligibility, blocking rules, and document linking semantics.
- **Document Persistence** (persistence): Stores and retrieves document metadata, version metadata, lifecycle state, storage references, checksums, and document-to-business-object links in owned data stores, while maintaining references to binary objects stored in object storage.
- **Document Event Handler** (messaging): Consumes platform events affecting document processing and state, reacts to scan outcomes and business workflow milestones, and emits document lifecycle and indexing events to the platform event bus.

## Data Owned
- None

## Consumed Events
- FileScanSucceeded
- FileScanFailedOrInfected
- RequestSubmitted
- ProcessDefinitionPublished
- CivilServantReviewCompleted
- ApprovalWorkflowCompleted

## Emitted Events
- DocumentRegistered
- DocumentVersionCreated
- DocumentLinkedToSubmission
- DocumentMetadataUpdated
- DocumentPublished
- DocumentArchived
- DocumentReadyForIndexing
- DocumentBlocked

## External Integrations
- None

## Security Controls
- Role-based access control for document creation, version upload, metadata updates, publication, archival, blocking, and retrieval operations.
- Authorization checks on document access based on document type, linked business context, and lifecycle state.
- Audit logging of document registration, version creation, metadata changes, publication, archival, blocking, link changes, and access to sensitive document operations.
- Encryption in transit for APIs, storage access, and messaging interactions.
- Encryption at rest for Aurora metadata stores and S3 document binaries.
- Integrity validation using checksums for uploaded document versions.
- Controlled access to document binaries through scoped service credentials and time-limited authorized retrieval mechanisms.

## Observability
- Structured application logs for document registration, version creation, metadata updates, lifecycle transitions, storage coordination, and event processing outcomes.
- Metrics for document registrations, version uploads, publish and archive actions, blocked documents, scan pass/fail counts, storage operation latency, and event processing throughput/failures.
- Distributed tracing across API requests, application workflows, persistence operations, object storage interactions, and event bus handlers.

## Open Questions
- None

## Confidence
high