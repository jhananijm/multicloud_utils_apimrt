# Architecture Overview - concourse_utils_apimrt

This document describes the architecture and internal flow of the repository `concourse_utils_apimrt`.

The goal of this repository is to support APIMRT automation by generating inventory, securely retrieving secrets, managing state, and producing Concourse pipeline YAML.

---

## High-level Flow

flowchart TD
    A[User or Concourse Job Trigger] --> B[Input Config and Parameters]

    B --> S[Secrets Retrieval - utils/get_secrets.py]
    B --> F[Inventory Fetch - utils/fetch_inventory.py]

    F --> N[Inventory Normalization - inventory_generation/inventory.py]

    N --> ST[State Management - utils/state_management.py]

    ST --> PB[Pipeline Builder - pipeline_builder/pipeline_builder.py]

    S --> KG[Key Generation - utils/key_gen.py]
    KG --> PB

    PB --> OUT[Output - Concourse Pipeline YAML]
    OUT --> C[Concourse Execution]
