# Shared Data Service

## Purpose
Manages canonical shared reference data that is static or changes infrequently and is reused by multiple services across the platform. The service governs dataset lifecycle, authority or global scope, item maintenance, version publication, and distribution of versioned snapshots and deltas so downstream services can build accurate local read models.

## Bounded Context
Shared Reference Data Management

## Service Type
domain

## Internal Components
- **Shared Data API** (api): Exposes query and administrative endpoints for retrieving shared datasets and for creating, updating, versioning, publishing, and deprecating datasets and items.
- **Shared Data Application Service** (application): Coordinates shared data use cases, validates requests, applies authorization and scope checks, orchestrates persistence and cache updates, and triggers publication of versioned change events.
- **Shared Data Domain Manager** (domain): Enforces business rules for dataset ownership, global versus authority-specific scope, item uniqueness, lifecycle transitions, version creation, publication eligibility, and deprecation handling.
- **Shared Data Repository** (persistence): Persists and retrieves authoritative shared datasets, dataset versions, items, and audit records from the primary relational store.
- **Shared Data Read Model / Cache** (persistence): Provides low-latency access to frequently requested shared datasets using optimized read storage and caching for published versions and commonly queried items.
- **Shared Data Event Handler** (messaging): Consumes explicit dataset-aware update requests from the event bus, maps them to application use cases, and ensures reliable processing of requested shared data changes.
- **Shared Data Distribution Publisher** (messaging): Publishes versioned snapshots and delta updates of shared datasets for downstream services to build local read models.

## Data Owned
- None

## Consumed Events
- DataUpdateRequested

## Emitted Events
- DataChanged
- DataAdded
- DataDepricated

## External Integrations
- None

## Security Controls
- None

## Observability
- None

## Open Questions
- Reviewer requested explicit dataset-aware and versioned consumed events, but the baseline defines only DataUpdateRequested as the consumed event. Should the baseline consumed event be retained as the canonical contract with a stricter payload schema, or should it be formally expanded into explicit events such as SharedDataSetCreatedRequested, SharedDataItemAddedRequested, SharedDataItemUpdatedRequested, SharedDataItemDeprecatedRequested, SharedDataSetVersionPublishRequested, and SharedDataSetDeprecatedRequested?
- Reviewer requested explicit emitted events SharedDataSetCreated, SharedDataSetVersionPublished, SharedDataItemAdded, SharedDataItemUpdated, SharedDataItemDeprecated, and SharedDataSetDeprecated. The baseline emitted events are DataChanged, DataAdded, and DataDepricated. Should the service emit both baseline events and the explicit dataset-aware events, or should the baseline event catalog be officially revised?

## Confidence
medium