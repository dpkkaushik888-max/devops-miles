# Process Documentation — AI-Assisted Development

This document captures how AI coding assistants (Claude Code / Windsurf Cascade) were used throughout the project, including methodology, key prompts, decision points, and where human judgement overrode AI suggestions.

---

## Methodology

### Workflow Pattern

Every major component followed this cycle:

```
1. PLAN   — Define what to build (human decision)
2. PROMPT — Describe the intent + constraints to the AI
3. REVIEW — Read every line of generated code critically
4. TEST   — Run it, break it, observe failure modes
5. REFINE — Iterate with the AI on fixes or improvements
```

The AI was never used as a black box. Every generated file was reviewed for:
- **Correctness** — Does it do what I asked?
- **Idempotency** — Can I run it twice without side effects?
- **Security** — Are there hardcoded secrets, open ports, or missing checks?
- **Style** — Is it clean, commented, and maintainable?

### AI as Pair Programmer, Not Autopilot

The challenge explicitly asks to *"show how you work WITH AI tooling"* and to *"use AI to build, not to run."* My approach:

- **I made all architectural decisions** — tool selection (Terraform + Ansible + GitHub Actions), network topology (bastion → Proxmox → VMs), golden template strategy, branch-based preview environments.
- **AI handled boilerplate and syntax** — YAML playbook structure, Terraform resource blocks, GitHub Actions workflow syntax, SSH config formatting.
- **I debugged and validated** — SSH proxy chain issues, cloud-init timing, NAT routing, concurrency race conditions were all debugged by me with AI assistance in generating diagnostic commands.

---

## Key AI Interactions by Stage

### Stage 1: Project Structure

**Prompt pattern:** "Create a project structure for a DevOps challenge that provisions VMs on Proxmox via Hetzner Cloud, deploys a Flask app, and automates everything with GitHub Actions."

**What AI provided:** Directory layout, initial README skeleton, plan.md template.

**Human override:** Restructured to separate `terraform/`, `ansible/`, `app/`, and `.github/workflows/` as top-level directories rather than the nested structure AI initially suggested. Cleaner separation of concerns.

---

### Stage 2: Terraform Configuration

**Prompt pattern:** "Write Terraform config to provision a bastion host and a Proxmox server on Hetzner Cloud with a private network between them. The bastion should be publicly accessible, Proxmox should only be reachable via the bastion."

**What AI provided:** Complete `main.tf` with `hcloud_server`, `hcloud_network`, `hcloud_firewall` resources.

**Human override:**
- AI initially used a single firewall for both servers. I split it into separate bastion and Proxmox firewalls with different rules.
- AI did not include the `hcloud_server_network` resource for attaching servers to the private network — I had to prompt specifically for that.
- Added `ip_range` for the private network subnet that AI omitted.

**Iteration example:**
> Me: "The Proxmox server needs a route to send private network traffic through the bastion. Add a route resource."
> AI: Generated `hcloud_network_route` with the bastion as gateway — correct on first try.

---

### Stage 3: Ansible Playbooks

This was the most AI-intensive stage. Each playbook required multiple iterations.

#### Golden Template (`create_template.yml`)

**Prompt pattern:** "Write an Ansible playbook that creates a Debian 12 VM template on Proxmox. It should download the cloud image, create a VM with cloud-init, pre-bake Python, Flask, gunicorn, sqlite3, and qemu-guest-agent, then convert it to a template. Make it idempotent."

**Key iterations:**
1. **First attempt** — AI generated a playbook that used `qm create` but forgot to import the disk with `qm importdisk`. Had to prompt: "The cloud image needs to be imported as a disk and attached to the VM before converting to template."
2. **Cloud-init baking** — AI suggested configuring cloud-init at clone time only. I asked: "Can we pre-bake the dependencies into the template using virt-customize so clones don't need to install anything?" This was the key insight that reduced clone-to-ready time from ~5 minutes to ~30 seconds.
3. **Idempotency** — AI's first version would fail if run twice (template already exists). Added `qm status 9000` check with `failed_when: false` and skip logic.

#### VM Creation (`proxmox_create_vm.yml`)

**Prompt pattern:** "Write a playbook to clone a VM from template 9000, configure cloud-init with a dynamic IP, set up NAT on the Proxmox host so the VM can reach the internet, and wait for SSH."

**Where AI struggled:**
- NAT configuration via iptables — AI generated correct MASQUERADE rules but forgot IP forwarding (`sysctl net.ipv4.ip_forward=1`). Caught during testing when the VM couldn't reach the internet.
- SSH readiness — AI used `wait_for` with port 22, but cloud-init hadn't finished configuring the SSH key yet. Added a retry loop with `ansible.builtin.command: ssh -o BatchMode=yes` to verify actual SSH login works.

#### App Deployment (`app_deploy.yml`)

**Prompt pattern:** "Deploy a Flask app with gunicorn as a systemd service. Copy files, install deps, run migration, create service, enable and start it. Add a smoke test."

**AI got this right on the first attempt.** Flask + gunicorn + systemd is a well-trodden path. Minor tweaks: changed the systemd service `ExecStart` to use the full path to gunicorn in the venv.

---

### Stage 4: Flask Application

**Prompt pattern:** "Create a minimal Flask app with: a form that takes a name, stores it in SQLite, returns a greeting. Add a /healthz endpoint that checks DB connectivity. Keep it simple — the pipeline is what matters."

**AI output was clean.** Added parameterised queries (safe from SQL injection), `render_template_string` with auto-escaping, and a proper healthz endpoint. No significant iteration needed.

**Test suite** — AI generated 19 tests covering GET, POST, edge cases (empty name, long name, XSS, special characters), healthz happy/unhappy paths. Used `tmp_path` fixture and mock for DB isolation. This was a highlight — the test quality was high on the first pass.

---

### Stage 5: GitHub Actions CI/CD

This was the most complex stage and required the most iteration.

**Prompt pattern:** "Create a GitHub Actions workflow with: (1) manual trigger to create the golden template, (2) test job on every push, (3) branch deploy — create a preview VM per branch, (4) branch cleanup — destroy VM on branch delete, (5) production deploy on push to master."

**Key iterations:**

1. **SSH key handling** — AI initially used `echo "$SSH_KEY" > ~/.ssh/key`. This broke because GitHub Actions secrets can have `\n` literals instead of actual newlines. Took 3 iterations to get the Python one-liner that handles both cases:
   ```python
   python3 -c "import os; k=os.environ['SSH_KEY'].replace('\r',''); ..."
   ```

2. **SSH proxy chain** — AI generated a flat SSH config. I needed a 3-hop chain: GitHub runner → bastion → Proxmox → app VM. The `ProxyCommand ssh -W %h:%p` nesting took 2 iterations to get right.

3. **Branch VM ID/IP derivation** — I proposed the hash-based approach: `VM_ID=$((1001 + (BRANCH_HASH % 7999)))`. AI implemented it but I had to specify the range constraints (1001-8999 for branches, 100 for production, 9000 for template).

4. **Concurrency control** — AI didn't initially add concurrency serialisation. After I noticed two branch deploys could race on Proxmox, I asked for `concurrency: group: proxmox-operations`. AI added it correctly with `cancel-in-progress: false` (important — we don't want to cancel a running deploy).

5. **Golden image auto-rebuild** — This was my idea, not the AI's. I asked: "Create a separate workflow that rebuilds the golden template when requirements.txt, app.py, or create_template.yml change on master." AI generated `build-golden-image.yml` with the correct `paths:` filter.

---

## Where AI Added the Most Value

1. **Ansible YAML syntax** — Ansible playbooks are verbose and error-prone. AI generated correct YAML structure consistently, saving significant time on module names, parameter formats, and indentation.

2. **GitHub Actions workflow syntax** — Complex `if:` conditions, `outputs`, `needs`, and artifact upload syntax. AI knew the current (v4) API surface well.

3. **Test generation** — The 19-test suite for the Flask app was generated in one prompt with excellent coverage of edge cases I might have skipped (XSS escaping, special characters, DB unavailability).

4. **Documentation** — The "Future Plan — Path to Production" section was drafted with AI assistance. I provided the 5-pillar framework and priorities; AI fleshed out each item with specific, actionable recommendations.

---

## Where Human Judgement Was Critical

1. **Architecture decisions** — Bastion + private network topology, golden template with pre-baked deps, branch-based preview environments (not in the original requirements — I chose to go beyond the ask).

2. **Security awareness** — Identified that AI-generated configs had `StrictHostKeyChecking no` everywhere. Kept it for the POC (documented the risk in Future Plan) but would never ship this to production.

3. **Debugging** — When cloud-init failed silently on first VM boot, I SSH'd into Proxmox manually, checked `/var/log/cloud-init.log` inside the VM, and identified the issue (missing `qemu-guest-agent` package). AI couldn't debug live infrastructure.

4. **Operational thinking** — Orphan VM detection (`validate_resources.yml`), daily cron audit, cleanup validation — these were all my additions based on experience with resource sprawl.

5. **Knowing when to stop** — The POC scope was intentional. AI would happily generate PostgreSQL configs, nginx reverse proxies, and Prometheus exporters if asked. I chose to document these as "Future Plan" items rather than over-engineering the POC.

---

## Tools Used

| Tool | Role |
|------|------|
| **Claude Code** | Primary AI coding assistant for all scripts, playbooks, and workflows |
| **Windsurf IDE** | Development environment with integrated AI (Cascade) |
| **Terminal** | SSH into bastion/Proxmox for manual debugging and validation |
| **GitHub Actions** | CI/CD execution and log inspection |
| **Proxmox Web UI** | Visual verification of VM states during development |

---

> This document was produced as part of the MILES DevOps Case Study to demonstrate the AI-assisted development process.
