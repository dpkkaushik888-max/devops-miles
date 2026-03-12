# DevOps MILES Challenge

End-to-end DevOps pipeline for VM lifecycle management on Proxmox VE, triggered by GitHub Actions, deploying a Python web application — all authored with AI coding assistants.

---

## Architecture

```
                        ┌──────────────────────────────────────────────────┐
                        │              Hetzner Cloud (Terraform)           │
                        │                                                  │
  GitHub Actions        │   ┌──────────┐    Private     ┌──────────────┐  │
  Runner ──── SSH ─────────►│  Bastion  │──  Network  ──►│  Proxmox VE  │  │
                        │   │  (cx22)   │  10.2.0.0/16  │   (cpx31)    │  │
                        │   │ public IP │               │  10.2.0.2    │  │
                        │   └──────────┘               └──────┬───────┘  │
                        │                                      │          │
                        │                          ┌───────────┼────────┐ │
                        │                          │  192.168.100.0/24  │ │
                        │                          │                    │ │
                        │                   ┌──────┴──────┐  ┌────────┐│ │
                        │                   │ Production  │  │ Branch ││ │
                        │                   │  VM (100)   │  │  VMs   ││ │
                        │                   │ Flask+SQLite│  │1001-8999│ │
                        │                   └─────────────┘  └────────┘│ │
                        │                          └───────────────────┘ │
                        └──────────────────────────────────────────────────┘
```

## Pipeline Flow

```
  git push (branch)          git push (master)          branch delete
       │                          │                          │
       ▼                          ▼                          ▼
  ┌─────────┐              ┌─────────┐              ┌──────────────┐
  │  Test   │              │  Test   │              │ Branch       │
  │ (pytest)│              │ (pytest)│              │ Cleanup      │
  └────┬────┘              └────┬────┘              │ (destroy VM) │
       │                        │                   └──────────────┘
       ▼                        ▼
  ┌──────────────┐     ┌────────────────┐
  │ Branch Deploy│     │ Production     │
  │ (clone VM,   │     │ Deploy         │
  │  deploy app, │     │ (VM 100,       │
  │  smoke test, │     │  deploy app,   │
  │  collect logs│     │  collect logs) │
  └──────────────┘     └────────────────┘
```

## Project Structure

```
devops-miles/
├── terraform/              # Hetzner Cloud infrastructure (bastion + Proxmox)
│   ├── main.tf             # Server, network, firewall resources
│   ├── variables.tf        # Input variables (API token, server types)
│   └── outputs.tf          # IPs, SSH commands
├── ansible/                # VM lifecycle and app deployment
│   ├── create_template.yml # Golden Debian 12 template (VM 9000)
│   ├── proxmox_setup.yml   # One-time Proxmox VE installation
│   ├── proxmox_create_vm.yml # Clone VM from template + cloud-init
│   ├── app_deploy.yml      # Deploy Flask app + gunicorn + smoke test
│   ├── destroy_vm.yml      # Stop and purge a VM
│   ├── validate_resources.yml # Audit for orphaned VMs
│   └── validate_cleanup.yml   # Verify VM was fully removed
├── app/                    # Python web application
│   ├── app.py              # Flask app (form + SQLite + /healthz)
│   ├── migrate.py          # DB schema migration
│   ├── requirements.txt    # Production deps (Flask, gunicorn)
│   ├── requirements-dev.txt # Dev deps (pytest, coverage)
│   └── tests/              # 19 tests (80%+ coverage gate)
├── .github/workflows/      # CI/CD automation
│   ├── deploy.yml          # Main pipeline (test → deploy → collect logs)
│   ├── build-golden-image.yml # Auto-rebuild template on dep changes
│   └── validate-resources.yml # Daily orphan VM audit (cron)
└── docs/                   # Deliverables
    ├── plan.md             # Project Goal Plan + reach goals
    ├── process.md          # AI interaction logs + methodology
    ├── reflection.md       # Lessons learned + problems overcome
    └── implemeantion.md    # Implementation log + Future Plan
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Golden template with pre-baked deps** | Cloning a template with Flask/gunicorn/sqlite3 already installed reduces deploy time from ~5 min to ~30 sec |
| **Branch-based preview environments** | Goes beyond the ask — each branch gets a persistent VM for debugging, not just ephemeral test-and-destroy |
| **Hash-based VM ID/IP** | Deterministic assignment from branch name avoids needing a central registry (collision risk documented) |
| **Concurrency serialisation** | `concurrency: group: proxmox-operations` prevents race conditions on the shared Proxmox host |
| **Orphan VM detection** | Daily cron audit catches VMs left behind by failed cleanups |
| **Auto-rebuild golden image** | Template rebuilds automatically when deps or app code change on master |

## Deliverables

| Deliverable | Location |
|-------------|----------|
| **Project Goal Plan** | [`docs/plan.md`](docs/plan.md) |
| **Working Solution** | This repository (Terraform + Ansible + GitHub Actions + Flask app) |
| **Process Documentation** | [`docs/process.md`](docs/process.md) — AI prompts, methodology, decision log |
| **Reflection** | [`docs/reflection.md`](docs/reflection.md) — Problems, lessons, growth |
| **Implementation Log** | [`docs/implemeantion.md`](docs/implemeantion.md) — Stage-by-stage progress + Future Plan |

## Quick Start

```bash
# 1. Provision infrastructure (one-time)
cd terraform
terraform init
terraform apply -var="hcloud_token=YOUR_TOKEN" -var="ssh_key_name=devops-miles"

# 2. Set up Proxmox VE (one-time, after Terraform)
cd ../ansible
ansible-playbook -i inventory.ini proxmox_setup.yml

# 3. Create golden template (one-time, or via GitHub Actions)
ansible-playbook -i inventory.ini create_template.yml

# 4. Deploy — push to any branch and GitHub Actions handles the rest
git push origin feature/my-branch   # → creates preview VM
git push origin master              # → deploys to production VM
```

## Access

```bash
# SSH tunnel to access the app (replace IPs from Terraform outputs)
ssh -i devops-miles-ssh-key \
    -L 5000:192.168.100.10:5000 \
    -J root@BASTION_IP \
    -N root@PROXMOX_IP

# Then open: http://localhost:5000
```

---

> All automation authored with AI coding assistants. See [`docs/process.md`](docs/process.md) for the full AI-assisted development methodology.
