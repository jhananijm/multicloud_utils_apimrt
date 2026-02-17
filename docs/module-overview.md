---

# ✅ `docs/module-overview.md`

# Module Overview - concourse_utils_apimrt

This document summarizes the main modules and their role in the repository.

---

## 1. utils/

### fetch_inventory.py
- Fetches raw inventory information from target environments
- Acts as the first stage in building an environment-aware pipeline

### get_secrets.py
- Retrieves secrets securely
- Keeps credentials out of the codebase and pipeline YAML

### state_management.py
- Stores and loads pipeline state between runs
- Supports idempotent pipeline generation and reuse of previous outputs

### key_gen.py
- Generates keys for secure authentication or encryption needs
- Used when automation requires signing/encryption

---

## 2. inventory_generation/

### inventory.py
- Converts raw inventory into a structured normalized model
- Provides consistent output format for pipeline_builder

---

## 3. pipeline_builder/

### pipeline_builder.py
- Generates Concourse pipeline YAML
- Builds pipeline jobs/resources based on inventory and configuration

### timer_backup.py
- Backup or scheduling utility
- Supports timed triggers or scheduled pipeline behavior

---

## 4. apimrt_utils/

Contains packaging-related utilities and reusable helpers for APIMRT automation.
This can be extended to become a shared Python library across automation projects.

---

## Suggested Future Enhancements
- Add CLI entrypoint (`python -m concourse_utils_apimrt`)
- Add schema validation for inventory output
- Add unit tests for pipeline builder
- Add logging standardization (structured logs with correlationId)

---
