# Scanning System Service (separate account)

## Purpose
Manages malware scan requests in an isolated scanning account by consuming ScanRequested events, securely staging files for scanning, orchestrating scanning workers that perform scanning tasks using the OPSWAT engine cluster, determining final scan verdicts, recording scan lifecycle metadata, and emitting scan result events.

## Bounded Context
Malware scanning orchestration within a dedicated scanning account, including scan request intake, secure file staging, worker-based scan execution using OPSWAT engines, verdict determination, and publication of scan outcome events.

## Service Type
domain

## Internal Components
- **Scan Operations API** (api): Provides internal operational endpoints to query scan job status, inspect scan outcomes, and support controlled retry and troubleshooting workflows for failed or stuck scans.
- **Scan Orchestration Application** (application): Consumes ScanRequested events, validates request context, creates scan jobs, coordinates secure staging and worker execution, manages scan state transitions, and triggers result finalization.
- **Scanning Worker Coordinator** (application): Allocates scan tasks to service-managed scanning workers, manages worker leases and execution windows, handles worker retries and timeout recovery, and ensures each requested file is processed exactly once in coordination with job state.
- **Scanning Worker Runtime** (application): Executes scanning tasks against staged files by invoking the OPSWAT engine cluster, collects raw engine responses, captures execution diagnostics, and returns normalized worker outcomes to the orchestration flow.
- **Verdict Evaluation Domain Service** (domain): Normalizes scanning worker and OPSWAT engine outputs, applies verdict rules, and determines whether the final scan result is clean or infected.
- **Scan Persistence Repository** (persistence): Persists scan jobs, execution attempts, scan results, and event publication state to support reliable processing, idempotency, auditability, and recovery.
- **Event Messaging Adapter** (messaging): Consumes ScanRequested events and publishes FileScannedClean and FileScannedInfected events with idempotent handling, retry support, and correlation metadata.
- **Secure File Staging Manager** (application): Manages isolated storage for inbound files, grants time-bounded worker access to staged artifacts, enforces retention and cleanup policies, and records artifact locations needed for scan execution and investigation.

## Data Owned
- None

## Consumed Events
- ScanRequested

## Emitted Events
- FileScannedClean
- FileScannedInfected

## External Integrations
- None

## Security Controls
- None

## Observability
- None

## Open Questions
- None

## Confidence
high