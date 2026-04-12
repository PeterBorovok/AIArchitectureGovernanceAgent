# Approval Workflow Service

## Purpose
Manages configurable multi-step approval workflows for business requests using AWS Step Functions orchestration. It tracks workflow instances and step progress, processes approval decisions, determines final outcomes, and emits workflow domain events when steps complete or when a request is approved or rejected.

## Bounded Context
Approval and workflow orchestration for multi-step request decisioning

## Service Type
domain

## Internal Components
- **Approval Workflow API** (api): Exposes service endpoints to start an approval workflow, query workflow status and history, and receive authorized operational commands related to workflow progression and administrative inspection.
- **Workflow Orchestration Application Service** (application): Coordinates workflow lifecycle operations, maps process types to workflow definitions, starts and advances AWS Step Functions executions, applies idempotent command handling, and orchestrates updates to workflow state and event publication.
- **Approval Workflow Domain Service** (domain): Encapsulates business rules for approval step sequencing, valid state transitions, final approval or rejection determination, and interpretation of incoming approval decisions and step completion outcomes.
- **Approval Workflow Repository** (persistence): Persists and retrieves workflow instances, step execution records, workflow definition references, and audit-relevant state changes required for reliable workflow progression and history queries.
- **Approval Messaging Adapter** (messaging): Consumes approval-related domain events, ensures idempotent event processing, translates events into application commands, and publishes ApprovalStepCompleted, RequestApproved, and RequestRejected events after successful state transitions.

## Data Owned
- None

## Consumed Events
- RequestApprovedByCivilServant
- ApprovalStepCompleted (if event driven between steps)

## Emitted Events
- RequestApproved
- RequestRejected
- ApprovalStepCompleted

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