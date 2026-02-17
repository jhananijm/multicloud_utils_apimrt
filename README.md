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
```
---

## Documentation
- [Architecture](docs/architecture.md)
- [Module Overview](docs/module-overview.md)
- [How to Run](docs/how-to-run.md)
- [Code Flow](docs/code-flow.md)
