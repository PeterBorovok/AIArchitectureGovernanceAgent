# Process Definition Service

## Purpose
Stores schemas and rules for processes and provides validation configuration, UI bundle metadata, and label configuration.

## Bounded Context
Process Definition

## Service Type
domain_service

## Internal Components
- **Process Definition API** (api): Exposes commands and queries for managing process definitions
- **Process Definition Application Service** (application): Coordinates process definition use cases such as publish, update, and retrieval
- **Process Definition Domain Service** (domain): Applies business rules for schema lifecycle, validation configuration, and publishing
- **Process Definition Repository** (persistence): Persists process definitions, schema versions, UI bundle references, and label configuration
- **Process Definition Event Publisher** (messaging): Publishes process schema lifecycle events

## Data Owned
- Process definitions
- Schema versions
- Validation configuration
- UI bundle metadata
- Label configuration

## Consumed Events

## Emitted Events
- ProcessSchemaPublished
- ProcessSchemaUpdated

## External Integrations
- Shared validation engine
- UI bundle storage

## Security Controls
- Authorization checks
- Audit trail
- Versioning controls

## Observability
- Structured logs
- Metrics
- Tracing
