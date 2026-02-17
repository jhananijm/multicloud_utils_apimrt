# concourse_utils_apimrt

A Python utility repository to support **APIMRT automation workflows** by generating inventories, managing state, retrieving secrets, and building **Concourse CI pipelines**.

This repository provides reusable components to standardize how APIMRT automation pipelines are generated and executed across environments.

---

## Key Features

- Fetch and normalize environment inventory
- Retrieve secrets securely (vault-based integration)
- Manage pipeline state (state persistence and reuse)
- Generate Concourse pipeline YAML programmatically
- Generate keys required for automation tasks

---

## Repository Structure

```text
concourse_utils_apimrt/
├── apimrt_utils/
│   └── setup.py
├── inventory_generation/
│   └── inventory.py
├── pipeline_builder/
│   ├── pipeline_builder.py
│   └── timer_backup.py
└── utils/
    ├── fetch_inventory.py
    ├── get_secrets.py
    ├── key_gen.py
    └── state_management.py


flowchart TD

    A[User / Concourse Job] --> B[Input Config / Parameters]

    %% Secrets
    B --> S[get_secrets.py<br/>Fetch secrets and credentials]
    
    %% Inventory
    B --> I[fetch_inventory.py<br/>Fetch raw inventory data]
    I --> INV[inventory.py<br/>Normalize and generate inventory model]

    %% State
    INV --> ST[state_management.py<br/>Persist state and reuse previous outputs]

    %% Pipeline generation
    ST --> P[pipeline_builder.py<br/>Generate Concourse pipeline YAML]

    %% Optional key generation
    S --> K[key_gen.py<br/>Generate encryption/signing keys]
    K --> P

    %% Output
    P --> OUT[Generated Concourse Pipeline YAML]
    OUT --> C[Concourse CI/CD Execution]
