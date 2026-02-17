# How to Run - concourse_utils_apimrt

This document explains the recommended execution flow for generating inventory and building Concourse pipelines using this repository.

> Note: Some scripts may require environment variables or access to internal services (Vault, cloud APIs, etc.).

---

## Prerequisites

- Python 3.x installed
- Access to required cloud accounts/subscriptions
- Access to Vault/secret store (if applicable)
- Required Python dependencies installed

---

## Setup (recommended)

Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Execution Flow (Recommended Order)

The typical execution order is:
	1.	Fetch secrets (if required)
	2.	Fetch inventory
	3.	Normalize inventory
	4.	Store/load state
	5.	Generate Concourse pipeline YAML

⸻
