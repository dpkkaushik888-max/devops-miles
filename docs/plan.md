# Project Goal Plan

## Objective

Build an end-to-end remote workflow that covers the full VM environment lifecycle — from a Git commit to a clean VM, through a deployed and tested application, and back to nothing — using Proxmox VE as the hypervisor, automated entirely through GitHub Actions.

---

## Core Requirements (from Case Study)

| # | Requirement | Status |
|---|-------------|--------|
| 1 | Provision a Hetzner server and install Proxmox VE | Done |
| 2 | Create a Linux VM template (clonable, repeatable) | Done |
| 3 | Pipeline: Spin up VM from template | Done |
| 4 | Pipeline: Deploy web app with backend DB | Done |
| 5 | Pipeline: Run smoke test | Done |
| 6 | Pipeline: Collect and store logs/test results | Done |
| 7 | Pipeline: Tear down VM cleanly | Done |
| 8 | Pipeline is reliable and repeatable (idempotent) | Done |
| 9 | Pipeline is scripted and deterministic (no AI at runtime) | Done |
| 10 | Use AI coding assistant to author scripts | Done |

---

## Tools Selected

| Tool | Purpose | Why This Tool |
|------|---------|---------------|
| **Terraform** | Infrastructure provisioning | Industry standard for cloud IaC; Hetzner provider is mature |
| **Ansible** | Configuration management, VM lifecycle | Agentless, SSH-native, ideal for Proxmox `qm` CLI orchestration |
| **GitHub Actions** | CI/CD pipeline | Native to the repo, free for public repos, good concurrency controls |
| **Flask** | Web application | Minimal, well-known, sufficient for a POC app |
| **SQLite** | Backend database | Zero-config, file-based, appropriate for single-VM POC |
| **Claude Code / Windsurf** | AI coding assistant | Used for all script authoring (see [process.md](process.md)) |

---

## Reach Goals

| Goal | Status | Notes |
|------|--------|-------|
| Branch-based preview environments | **Achieved** | Each branch gets a persistent VM with the app deployed. Not just ephemeral test-and-destroy. |
| Golden template with pre-baked dependencies | **Achieved** | `virt-customize` bakes Flask, gunicorn, sqlite3 into the template. Clones are ready in ~30 sec. |
| Auto-rebuild golden image on dependency changes | **Achieved** | `build-golden-image.yml` triggers on changes to requirements.txt, app.py, or create_template.yml. |
| Orphan VM detection and audit | **Achieved** | `validate-resources.yml` runs daily via cron and on-demand. Catches VMs left behind by failed cleanups. |
| Test suite with coverage gate | **Achieved** | 19 tests, 80% coverage minimum enforced in CI. JUnit XML + HTML coverage uploaded as artifacts. |
| Health check endpoint | **Achieved** | `/healthz` checks DB connectivity, returns JSON status. |
| Job timeouts on all pipeline jobs | **Achieved** | 10-20 minute timeouts prevent hung jobs from blocking the concurrency queue. |
| Production hardening assessment | **Achieved** | 40+ items across 5 pillars in [implemeantion.md](implemeantion.md) "Future Plan" section. |
| Parameterised pipeline for multiple environments | Not started | Documented as future work. Would require environment-specific variable files. |
| Automated monitoring and alerting | Not started | Documented as future work (Prometheus + Grafana). |
| Horizontal scaling | Not started | Documented as future work (Proxmox cluster, load balancer). |

---

## Deliverables

| Deliverable | Location | Description |
|-------------|----------|-------------|
| **Project Goal Plan** | This file | Goals, tools, reach goals, and status |
| **Working Solution** | Repository root | Terraform + Ansible + GitHub Actions + Flask app |
| **Process Documentation** | [`docs/process.md`](process.md) | AI prompts, methodology, decision log, key interactions |
| **Reflection** | [`docs/reflection.md`](reflection.md) | Problems encountered, lessons learned, what I'd do differently |
| **Implementation Log** | [`docs/implemeantion.md`](implemeantion.md) | Stage-by-stage progress + Future Plan (path to production) |

---

## Timeline

| Phase | Duration | What was done |
|-------|----------|---------------|
| Infrastructure Foundation | ~1.5 hrs | Terraform config, Hetzner provisioning, Proxmox setup |
| Pipeline Development | ~3 hrs | Ansible playbooks, GitHub Actions workflows, SSH chain, golden template |
| Application & Tests | ~0.5 hrs | Flask app, migration script, 19-test suite |
| Documentation & Polish | ~1 hr | Process docs, reflection, README, log collection, version pinning |
