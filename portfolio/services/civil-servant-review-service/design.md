# Civil Servant Review Service

## Purpose
Allows a Civil Servant to review submitted request fields, provide per-field comments, confirm or reject individual fields, record an overall review comment, and finalize the review outcome for a submitted request in alignment with the request submission lifecycle.

## Bounded Context
Civil Servant request review and adjudication

## Service Type
domain

## Internal Components
- **Review API** (api): Exposes endpoints to retrieve review state, submit or update per-field comments, record per-field confirm or reject decisions, submit overall review comments, and finalize the civil servant review outcome for an eligible submitted request.
- **Review Application Service** (application): Coordinates review use cases, validates that reviews are only created or changed for requests in valid lifecycle states, enforces draft versus finalized review rules, orchestrates persistence, and triggers event publication after successful transactions.
- **Review Domain Engine** (domain): Implements domain rules for field-level review decisions, comment updates, overall request approval or rejection, lifecycle consistency with the underlying submitted request, and immutability constraints after review finalization where applicable.
- **Review Repository** (persistence): Persists and retrieves review aggregates, per-field review decisions, and review audit entries with transactional consistency for business operations and compliance traceability.
- **Review Event Publisher** (messaging): Publishes domain events when review comments change and when a request is approved or rejected by the civil servant, and consumes submission lifecycle events to initialize, update, or invalidate review state as needed.

## Data Owned
- None

## Consumed Events
- RequestSubmitted
- RequestUpdated
- RequestWithdrawn

## Emitted Events
- RequestApprovedByCivilServant
- RequestRejectedByCivilServant
- RequestCommentChanged

## External Integrations
- None

## Security Controls
- None

## Observability
- None

## Open Questions
- None

## Confidence
medium