---

# ✅ `docs/code-flow.md`

# Code Flow - concourse_utils_apimrt

This document explains the end-to-end code execution flow in detail.

---

## Step 1: Inputs

Inputs typically include:
- environment name (dev/test/prod)
- tenant or customer identifier
- cloud subscription/project identifiers
- pipeline configuration parameters
- secrets source configuration (vault)

---

## Step 2: Secrets retrieval

`utils/get_secrets.py`

Secrets are retrieved early to ensure:
- secure access to cloud providers
- secure access to artifact repositories
- secure access to internal services

---

## Step 3: Inventory fetch

`utils/fetch_inventory.py`

This step gathers environment metadata required to generate correct pipelines.

---

## Step 4: Inventory normalization

`inventory_generation/inventory.py`

The raw inventory is converted into a normalized model which acts as a contract.

Benefits:
- stable downstream pipeline generation
- consistency across environments
- reduces coupling to discovery implementation

---

## Step 5: State persistence

`utils/state_management.py`

This step stores inventory and pipeline state to enable:
- reproducibility
- rollback and traceability
- idempotent regeneration

---

## Step 6: Pipeline YAML generation

`pipeline_builder/pipeline_builder.py`

Pipeline builder uses:
- normalized inventory
- state
- pipeline configuration

Output:
- Concourse pipeline YAML

---

## Step 7: Concourse execution

Pipeline YAML is applied via Concourse (`fly set-pipeline`).
Execution occurs inside Concourse workers.

---

## Full Flow Diagram

```mermaid
flowchart TD
    A[Input Parameters] --> B[get_secrets.py]
    A --> C[fetch_inventory.py]
    C --> D[inventory.py]
    D --> E[state_management.py]
    E --> F[pipeline_builder.py]
    F --> G[Generated Concourse YAML]
    G --> H[Concourse Pipeline Execution]
