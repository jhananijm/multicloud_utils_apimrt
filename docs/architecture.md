# Architecture Overview - concourse_utils_apimrt

This document describes the architecture and internal flow of the repository `concourse_utils_apimrt`.

The goal of this repository is to support APIMRT automation by generating inventory, securely retrieving secrets, managing state, and producing Concourse pipeline YAML.

---

## High-level Flow

```mermaid
flowchart TD

    A[User / Concourse Job Trigger] --> B[Input Config / Parameters]

    B --> S[Secrets Retrieval<br/>utils/get_secrets.py]
    B --> F[Inventory Fetch<br/>utils/fetch_inventory.py]

    F --> N[Inventory Normalization<br/>inventory_generation/inventory.py]

    N --> ST[State Management<br/>utils/state_management.py]

    ST --> PB[Pipeline Builder<br/>pipeline_builder/pipeline_builder.py]

    S --> KG[Key Generation (optional)<br/>utils/key_gen.py]
    KG --> PB

    PB --> OUT[Output: Concourse Pipeline YAML]
