# Notification Service

## Purpose
Consumes request lifecycle events and sends user-facing notifications through email and SMS channels via SendGrid. The service manages notification orchestration, template and channel selection, idempotent event handling, delivery execution, retry handling, and audit-ready notification history for request-related communications.

## Bounded Context
Outbound notifications for request lifecycle events

## Service Type
domain

## Internal Components
- **Notification Operations API** (api): Exposes internal operational endpoints for notification status lookup, failed delivery inspection, controlled retry or replay actions, and health/readiness checks for support and platform operations.
- **Notification Orchestrator** (application): Coordinates notification processing from consumed events by enforcing idempotency, resolving recipients and templates, creating notification records, invoking delivery providers, handling retries, and updating final notification outcomes.
- **Notification Policy Engine** (domain): Applies business rules to determine whether a notification should be sent for a given request event, which communication channel should be used, and which template should be selected.
- **Notification Repository** (persistence): Persists notification records, delivery attempts, and idempotency markers, and provides query and update access needed for operations, retries, and audit history.
- **Request Event Consumer** (messaging): Subscribes to request lifecycle events, validates message envelopes, extracts correlation and causation identifiers, normalizes event payloads, and forwards them for notification processing.
- **Notification Event Publisher** (messaging): Publishes notification lifecycle events after creation and send completion so downstream services can react to notification fulfillment and status changes when needed.

## Data Owned
- None

## Consumed Events
- RequestSubmitted
- RequestRejectedByCivilServant
- RequestRejectedDueToMalware
- RequestReturnedForFixes
- RequestApproved
- RequestStatusChanged
- RequestUpdated

## Emitted Events
- NotificationCreated
- NotificationSent
- NotificationDeliveryFailed

## External Integrations
- None

## Security Controls
- Restrict operational API access using service-to-service authentication and role-based access control.
- Encrypt notification data in transit and at rest, including stored provider references and response metadata.
- Minimize and redact sensitive recipient and message data in logs, traces, and operational API responses.
- Maintain immutable audit trails for notification creation, retries, delivery state changes, and operator-initiated replay actions.

## Observability
- Structured logs for consumed events, notification decisions, persistence actions, provider requests, delivery outcomes, emitted notification events, and retry processing.
- Metrics for events consumed, notifications created, notifications sent, delivery failures, retries, duplicate events ignored, provider latency, and consumer lag.
- Distributed tracing across event consumption, orchestration, persistence, SendGrid calls, and emitted notification lifecycle events.
- Alerting on sustained delivery failures, provider error spikes, abnormal retry volume, and backlog growth in event consumption.

## Open Questions
- Should NotificationSent represent provider acceptance by SendGrid, or only a stronger downstream delivery confirmation if such confirmation becomes available for the configured channel?
- Do downstream consumers require a more granular event such as NotificationRetried, or are NotificationCreated, NotificationSent, and NotificationDeliveryFailed sufficient for current platform needs?

## Confidence
high