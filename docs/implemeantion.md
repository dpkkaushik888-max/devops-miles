# Implementation Log

This file tracks all steps, decisions, and progress for the DevOps MILES challenge implementation.

## Scope & Intent

This project is a **Proof of Concept (POC)** assignment designed to demonstrate how a modern DevOps pipeline can be architected and automated end-to-end. The goal is not a production-ready system, but to show the ability to:

- Provision cloud infrastructure as code (Terraform on Hetzner Cloud)
- Automate VM lifecycle on a self-hosted hypervisor (Proxmox)
- Build a branch-based preview environment pipeline (GitHub Actions)
- Deploy and manage a web application using configuration management (Ansible)
- Think critically about what it would take to harden this for production

The **Future Plan** section at the bottom captures exactly that — a senior-level assessment of what would be required to take this from POC to production grade across the five pillars of well-architected systems.

---

## Stage 1: Project Structure & Documentation
- Created project directories: terraform, ansible, app, .github/workflows, docs
- Added README.md and plan.md
- Status: Completed

## Stage 2: Terraform Configuration
- Created terraform/README.md, main.tf, variables.tf, outputs.tf
- Defined Hetzner server, firewall, and network resources
- Status: In Progress

## Stage 2: SSH Key Generation
- Generated new SSH key pair (ed25519) for project: devops-miles-ssh-key, devops-miles-ssh-key.pub
- Added .gitignore entry to prevent SSH keys from being pushed to remote git
- Status: Completed

## Stage 3: Ansible Playbooks
- Created ansible/README.md, proxmox_setup.yml, app_deploy.yml, proxmox_create_vm.yml, destroy_vm.yml
- Playbooks cover Proxmox setup, VM creation, app deployment, and VM teardown
- Status: Completed

## Stage 4: Python Web App
- Created app/README.md, app.py, migrate.py, requirements.txt
- Flask app with SQLite backend: takes name, stores in DB, returns greeting
- Status: Completed

## Stage 5: GitHub Actions CI/CD
- Branch push → create preview VM on Proxmox (idempotent)
- Branch delete → destroy preview VM
- Master push → destroy + recreate production VM (immutable pattern)
- SSH routing via ~/.ssh/config with ProxyCommand chain (bastion → proxmox → app VM)
- VM ID and IP derived deterministically from branch name hash
- Status: Completed

---

---

## Future Plan — Path to Production

> **Context:** The items below are out of scope for this POC. They represent what a senior DevOps engineer would prioritise to evolve this pipeline into a production-grade system. They are intentionally documented here to demonstrate awareness of production concerns beyond the immediate assignment.
>
> Reviewed across 5 pillars: Security, Cost, Monitoring, Operational Excellence, Architecture.

---

### 🔐 Security

#### Critical
- [ ] **Remove root SSH access** — Create dedicated `ansible` service account on bastion and proxmox with sudo. Never SSH as root in CI/CD.
- [ ] **Restrict bastion firewall** — Lock SSH (port 22) to known CIDRs (office IPs, GitHub Actions IP ranges) instead of `0.0.0.0/0`.
- [ ] **Enable host key verification** — Remove `UserKnownHostsFile /dev/null` and `StrictHostKeyChecking no`. Pre-populate `known_hosts` at provisioning time via Terraform outputs.
- [ ] **Add Terraform remote state with encryption** — Use S3/GCS backend with server-side encryption and state locking (DynamoDB/GCS lock). Local state is lost and contains plaintext secrets.
- [ ] **Rotate SSH keys on schedule** — Implement key rotation via GitHub Actions on a cron schedule. Current key has no expiry.
- [ ] **Serve app over HTTPS** — Add TLS via nginx reverse proxy with Let's Encrypt (certbot). Flask dev server with HTTP is not acceptable for production.
- [ ] **Run Flask behind gunicorn** — Replace `python3 app.py` in systemd service with `gunicorn -w 4 -b 127.0.0.1:5000 app:app`. Flask's dev server is single-threaded and not production-safe.

#### High
- [ ] **Verify cloud image checksum** — Add SHA256 checksum verification after downloading the Ubuntu cloud image in `proxmox_create_vm.yml`. Currently downloaded without integrity check.
- [ ] **Add firewall rules to app VMs** — Currently only NAT is configured. Add ufw/iptables rules to allow only port 5000 (or 443) and SSH from proxmox subnet, block everything else.
- [ ] **Pin Ansible and Python dependency versions** — `apt-get install -y ansible` and `Flask` in requirements.txt are unpinned. Pin to specific versions to prevent supply chain issues.
- [ ] **Add secret scanning to CI** — Add `truffleHog` or GitHub secret scanning to PRs to catch accidentally committed credentials.
- [ ] **Enable branch protection on master** — Require PR reviews, passing CI, and no force-pushes to master.
- [ ] **Store Hetzner API token in Vault or GitHub secret** — Never pass as CLI arg or env var in plaintext shell history.
- [ ] **Disable password authentication on all VMs** — Verify `PasswordAuthentication no` in sshd_config on bastion, proxmox, and app VMs.
- [ ] **Enable KVM hardware virtualisation** — Remove `--kvm 0` flag in VM creation. Running VMs without hardware virtualisation is a security and performance regression.

#### Medium
- [ ] **Add SQLite encryption at rest** — Use SQLCipher or migrate to PostgreSQL with encrypted storage for any PII/sensitive data.
- [ ] **Implement least-privilege IAM** — Separate GitHub Actions secrets per environment (preview vs production). Preview VMs should not have credentials that touch prod.
- [ ] **Add CORS and CSP headers** — Flask app has no security headers. Add via nginx or Flask-Talisman.
- [ ] **Sanitise user input in app.py** — The `name` field is parameterised (safe from SQLi) but add length validation and XSS protection before rendering.

---

### 💰 Cost

#### Critical
- [ ] **Add TTL/auto-expiry for preview VMs** — A branch that is never deleted leaves a VM running forever. Add a scheduled GitHub Actions job to destroy VMs for branches with no commits in >7 days.
- [ ] **Use Proxmox VM templates (clone, not create)** — Current flow re-downloads the Ubuntu cloud image and recreates from scratch every time. Create a golden template once and clone it. This cuts VM provisioning from ~5 min to ~30 sec and saves bandwidth.
- [ ] **Right-size Proxmox server** — Evaluate whether `cpx31` (4 vCPU, 8GB RAM) is appropriate. For a small team, `cpx21` may suffice. Add auto-scaling or monitoring before committing to a size.

#### High
- [ ] **Set resource quotas on preview VMs** — Limit branch preview VMs to 1 vCPU and 1GB RAM vs production's 2 vCPU / 2GB. Add `--memory` and `--cores` as configurable extra-vars with sensible defaults.
- [ ] **Set up Hetzner budget alerts** — Configure billing alerts in Hetzner Cloud console to notify at 80% of monthly budget. Add to runbook.
- [ ] **Cache cloud image on Proxmox host** — `get_url` already uses a fixed path so re-downloads are skipped if file exists — but add a checksum to detect stale images and only re-download when a new version is available.
- [ ] **Consider LXC containers for preview environments** — LXC containers on Proxmox start in seconds, use a fraction of RAM, and share the host kernel. Full QEMU VMs are overkill for short-lived preview envs.

#### Medium
- [ ] **Add max concurrent preview VM limit** — Cap the number of live preview VMs (e.g., 5) in the workflow to prevent runaway cost from many open branches. Fail fast with a clear message if limit is hit.
- [ ] **Destroy preview VM on PR merge, not just branch delete** — GitHub doesn't auto-delete branches on merge by default. Add auto-delete branch setting in repo, or add a `pull_request closed` trigger alongside `delete`.

---

### 📊 Monitoring

#### Critical
- [ ] **Add application health check endpoint** — Add `/healthz` route to `app.py` that checks DB connectivity and returns `{"status": "ok"}`. Use this for all liveness/readiness probes instead of `/`.
- [ ] **Set up external uptime monitoring** — Use UptimeRobot (free) or Grafana Cloud to ping the production app every 60s and alert on downtime. Currently there is zero visibility into production health.
- [ ] **Add log aggregation** — Ship systemd journal logs from app VMs to a central sink (Loki + Grafana, or CloudWatch Logs). Logs are currently lost when VMs are destroyed.

#### High
- [ ] **Add Prometheus + Grafana** — Deploy on Proxmox host or a dedicated VM. Instrument Flask app with `prometheus-flask-exporter`. Track: request rate, error rate, latency (RED metrics).
- [ ] **Add Proxmox host monitoring** — Monitor Proxmox node CPU, RAM, disk I/O, and VM count via Prometheus `node_exporter` or Proxmox's built-in metrics endpoint.
- [ ] **Add GitHub Actions failure notifications** — Post to Slack/Teams on workflow failure using `slackapi/slack-github-action`. Currently failures are silent unless someone checks GitHub.
- [ ] **Monitor disk usage on Proxmox** — VM images accumulate. Alert when Proxmox local storage exceeds 80% capacity.

#### Medium
- [ ] **Add structured logging to Flask app** — Replace implicit Flask logging with structured JSON logs (`python-json-logger`). Include request ID, user, timestamp, response code.
- [ ] **Add deployment tracking** — Post deployment events to a monitoring tool (Grafana annotations, Datadog events) so you can correlate deployments with incidents.
- [ ] **Add smoke test coverage** — Current smoke test only checks HTTP 200 on `/`. Add tests for: POST creates a record, DB is reachable, response time < 500ms.

---

### ⚙️ Operational Excellence

#### Critical
- [ ] **Separate Proxmox setup from VM creation** — `proxmox_create_vm.yml` removes enterprise repos, installs tools, and configures NAT on every run. This one-time setup should be in `proxmox_setup.yml` only, run once at infra provisioning. Mixing it with VM creation causes unnecessary drift risk.
- [ ] **Add Terraform to CI pipeline** — Terraform is currently run manually. Add a CI job: `terraform plan` on PR (post plan as comment), `terraform apply` on merge to master via CI. Never apply manually.
- [ ] **Fix IP collision risk** — The branch VM IP is `192.168.100.$((20 + hash % 235))`. Two branches can hash to the same IP. Track allocated IPs in a GitHub Actions cache or a simple file in a dedicated repo branch as a lock file.
- [ ] **Add job timeout** — GitHub Actions jobs have no timeout set. A hung Ansible playbook blocks the concurrency queue indefinitely. Add `timeout-minutes: 30` to each job.
- [ ] **Add database backup before VM destroy** — `destroy_vm.yml` purges the VM and all data. Add a task to dump the SQLite DB and upload to S3/object storage before destruction (for production VM only).

#### High
- [ ] **Implement zero-downtime production deploys** — Current pattern (destroy → create) causes downtime on every master push. Use blue/green: create new VM, health check, swap DNS/load balancer, then destroy old. Or use in-place deploy with `app_deploy.yml` without VM recreation.
- [ ] **Pin Ansible version in CI** — Replace `apt-get install -y ansible` with a specific version: `pip install ansible==9.x.x`. Unpinned installs can break without notice.
- [ ] **Add Ansible linting to CI** — Run `ansible-lint` on all playbooks in a PR check before deployment. Catches issues before they reach infrastructure.
- [ ] **Add Terraform linting and validation** — Run `terraform validate` and `tflint` in CI on every PR touching `terraform/`.
- [ ] **Add rollback mechanism** — On failed production deploy, automatically re-run the previous working deploy. Tag each production deploy in git and store the last-known-good VM ID.
- [ ] **Add VM creation pre-flight checks** — Before creating a VM, verify: Proxmox has enough free RAM/disk, the requested VM ID is not already taken, the target IP is not already in use.
- [ ] **Set systemd service resource limits** — Add `MemoryMax=512M` and `CPUQuota=50%` to the systemd service file to prevent a rogue app from consuming the entire VM.
- [ ] **Add graceful shutdown to Flask app** — Handle `SIGTERM` in `app.py` to finish in-flight requests before shutdown. Required for zero-downtime restarts.

#### Medium
- [ ] **Create a runbook** — Document: how to SSH into each environment, how to check VM status, how to manually destroy a stuck VM, how to rotate SSH keys, how to restore from backup.
- [ ] **Add Dependabot** — Enable Dependabot for GitHub Actions (`actions/checkout`, etc.) and Python dependencies to get automatic security update PRs.
- [ ] **Add Terraform output validation** — After `terraform apply`, validate that bastion IP and Proxmox IP match the hardcoded values in `inventory.ini` and workflow env vars. Currently a mismatch would silently break all deployments.

---

### 🏛️ Architecture

#### Critical
- [ ] **Replace SQLite with PostgreSQL** — SQLite is a single-file DB with no network access, no replication, and limited concurrent write performance. Use PostgreSQL on a dedicated VM or managed service (Hetzner managed DB). Add connection pooling with PgBouncer.
- [ ] **Add nginx reverse proxy** — Flask should not be exposed directly. Add nginx in front to handle: TLS termination, static file serving, rate limiting, request buffering, and access logging.
- [ ] **Remove hardcoded IPs from all files** — `178.104.26.115` and `10.2.0.2` appear hardcoded in workflows, playbooks, and inventory. These should come from Terraform outputs stored in GitHub Actions variables or a config file generated by Terraform.

#### High
- [ ] **Build a Proxmox VM template once** — Instead of downloading the cloud image and creating VMs from scratch each time, create a Proxmox template (`qm template`) after first setup and clone it (`qm clone`) for all subsequent VMs. Reduces provisioning time from minutes to seconds.
- [ ] **Add a load balancer / reverse proxy in front of production** — nginx or HAProxy on the bastion or a dedicated VM. Enables zero-downtime blue/green deploys and future horizontal scaling.
- [ ] **Add DNS** — All access is currently via IP. Add DNS records (even internal ones via `/etc/hosts` or a lightweight DNS server) for environments. e.g. `preview-<branch>.internal`, `app.internal`.
- [ ] **Decouple Proxmox infrastructure from app VMs in Terraform** — Terraform manages bastion and Proxmox server, but VMs inside Proxmox are managed by Ansible. Consider using the Terraform Proxmox provider (`bpg/proxmox`) to manage VMs too, giving full infrastructure-as-code with state tracking.
- [ ] **Add Proxmox cluster for HA** — Single Proxmox node is a SPOF. For production, a 3-node Proxmox cluster with shared storage (Ceph or NFS) allows VM live migration and HA restart on node failure.

#### Medium
- [ ] **Move to container-based app deployment** — Package the Flask app as a Docker image. Deploy via Docker or Podman on the VM. This enables: reproducible builds, image versioning, faster deploys, easier rollback (tag-based).
- [ ] **Add GitHub Environments** — Define `preview` and `production` GitHub Environments with protection rules (require approval for production deploys, environment-specific secrets).
- [ ] **Implement infrastructure drift detection** — Run `terraform plan` on a daily cron and alert if drift is detected between desired and actual state.
- [ ] **Add network segmentation** — All preview VMs share `192.168.100.0/24` with production. Isolate production on a separate subnet/VLAN. Preview VMs should not be able to reach production DB or services.
- [ ] **Tag all Hetzner resources** — Add labels to Hetzner servers (`env=production`, `project=devops-miles`) for cost attribution, filtering, and lifecycle management.

---

## Future Plan — Prioritisation Summary

| Priority | Item |
|----------|------|
| P0 — Do before any real traffic | HTTPS/TLS, gunicorn, remove root SSH, PostgreSQL, remote Terraform state |
| P1 — Do before team scales | Branch protection, VM templates, job timeouts, uptime monitoring, no hardcoded IPs |
| P2 — Do in next sprint | Log aggregation, Prometheus/Grafana, zero-downtime deploys, Ansible lint in CI |
| P3 — Planned improvements | Proxmox HA cluster, Docker-based deploys, GitHub Environments, DNS |

---

> This Future Plan was produced as part of the POC review on 2026-03-12. It demonstrates the engineering judgement required to bridge a working proof-of-concept to a system that could carry real production workloads.
