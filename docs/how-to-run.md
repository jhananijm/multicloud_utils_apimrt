# How to Run - concourse_utils_apimrt

This document provides example usage patterns for running the utilities in this repository.

> Note: Exact command-line parameters may vary depending on internal implementation.
> These examples demonstrate the recommended execution flow.

---

## Recommended Execution Order

1. Retrieve secrets
2. Fetch inventory
3. Normalize inventory
4. Manage/load state
5. Generate Concourse pipeline YAML

---

## 1. Setup environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

---

## How to Run (6-Step Execution Flow)

This repository follows a simple execution flow to generate inventory and build Concourse pipelines.

### Step 1: Setup Python environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
