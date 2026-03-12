# Reflection — Lessons Learned

This document captures the problems encountered, solutions found, and lessons learned during the DevOps MILES challenge.

---

## Problems Encountered

### 1. SSH Proxy Chain Complexity

**Problem:** The architecture requires a 3-hop SSH chain: GitHub Actions runner → bastion (public IP) → Proxmox host (private network) → app VM (NAT'd subnet). Getting this to work reliably in a CI/CD environment was the hardest infrastructure challenge.

**What went wrong:**
- First attempt used inline SSH options (`-o ProxyCommand=...`) which became unreadable and brittle with nested quoting.
- GitHub Actions runners have no persistent SSH config, so the full chain must be reconstructed on every job.
- The SSH key stored in GitHub Secrets had `\n` encoded as literal backslash-n characters rather than actual newlines, causing `Permission denied` errors that were difficult to diagnose.

**Solution:**
- Wrote a dedicated "Configure SSH" step that generates a proper `~/.ssh/config` with `ProxyCommand` directives for each hop.
- Used a Python one-liner to handle both `\n` formats when writing the SSH key to disk.
- This pattern is now reused identically across all four jobs (create-template, branch-deploy, branch-cleanup, production-deploy).

**Lesson:** SSH key serialisation in CI/CD secrets is a common gotcha. Always test the actual key bytes, not just whether the file exists.

---

### 2. Cloud-Init Timing and VM Readiness

**Problem:** After cloning a VM from the template and starting it, the VM takes 30-60 seconds to become SSH-ready. Cloud-init must finish configuring the hostname, SSH keys, and network before Ansible can connect.

**What went wrong:**
- First attempt used Ansible's `wait_for` module to check port 22. The port opened before cloud-init finished writing the SSH authorized_keys file, causing `Permission denied` on the next task.
- Second attempt added a fixed `pause: 30` which worked but was fragile and slow.

**Solution:**
- Used `wait_for` for port 22 (quick TCP check), followed by an Ansible `command` task that actually attempts an SSH login with `BatchMode=yes`. This retries until the full SSH handshake succeeds, which only happens after cloud-init completes.
- Reduced average wait time from 30s (fixed pause) to ~15s (retry loop exits as soon as ready).

**Lesson:** "Port open" does not mean "service ready." Always verify the full connection path, especially with cloud-init VMs.

---

### 3. NAT and IP Forwarding on Proxmox

**Problem:** App VMs live on an internal subnet (`192.168.100.0/24`) and need internet access (for `apt` during provisioning) and inbound access (for SSH from the runner via Proxmox).

**What went wrong:**
- Set up MASQUERADE iptables rules but forgot to enable IP forwarding (`net.ipv4.ip_forward=1`). VMs could receive traffic but couldn't route responses back.
- The iptables rules were not persistent across Proxmox reboots. After a Proxmox restart, all VMs lost internet connectivity.

**Solution:**
- Added `sysctl -w net.ipv4.ip_forward=1` and persisted it in `/etc/sysctl.d/`.
- Made the NAT configuration part of the VM creation playbook so it's reapplied on every run (idempotent via iptables `-C` check before `-A`).

**Lesson:** NAT rules and kernel parameters should be applied and verified as part of infrastructure provisioning, not assumed to persist.

---

### 4. Concurrency Race Conditions on Proxmox

**Problem:** Two developers pushing to different branches simultaneously would trigger two `branch-deploy` jobs that both try to run Ansible against Proxmox at the same time. Proxmox's `qm clone` and `qm start` operations can conflict when run concurrently.

**What went wrong:**
- During testing, two simultaneous deploys caused a Proxmox lock error: `unable to create VM — got lock 'clone'`. One job failed, leaving a half-created VM.

**Solution:**
- Added `concurrency: group: proxmox-operations` with `cancel-in-progress: false` to the workflow. This serialises all Proxmox-touching jobs so they run one at a time.
- Chose `cancel-in-progress: false` deliberately — we don't want to cancel a deploy that's already provisioning a VM. Jobs queue instead.

**Lesson:** Any shared mutable resource (Proxmox, a database, a deployment target) needs serialisation in CI/CD. GitHub Actions' `concurrency` groups are the right tool.

---

### 5. VM ID and IP Collision Risk

**Problem:** Branch VMs get their ID and IP from a hash of the branch name: `VM_ID=$((1001 + (BRANCH_HASH % 7999)))`. Two different branch names can hash to the same value.

**What went wrong:**
- Identified during code review, not during a live collision. But the probability is non-trivial: with 50 active branches, there's a ~15% chance of at least one collision (birthday problem).

**Solution (documented, not implemented):**
- For the POC, accepted the risk and documented it in the Future Plan as a known issue.
- Production fix would use a lock file or GitHub Actions cache to track allocated VM IDs and retry with a different offset on collision.

**Lesson:** Hash-based resource allocation is convenient for POCs but needs collision handling for production. Always calculate the birthday problem probability for your expected scale.

---

### 6. Golden Template Staleness

**Problem:** If someone updates `requirements.txt` or `app.py` but forgets to rebuild the golden template, new VMs will be cloned from a stale template with old dependencies.

**What went wrong:**
- During development, I updated Flask and forgot to rebuild the template. The deploy succeeded but the app was running an older version of Flask than expected.

**Solution:**
- Created `build-golden-image.yml` — a GitHub Actions workflow that automatically rebuilds the golden template whenever `app/requirements.txt`, `app/app.py`, or `ansible/create_template.yml` change on the master branch.
- The workflow destroys the old template first (`qm destroy 9000 --purge`) to force a clean rebuild.

**Lesson:** Pre-baked dependencies in VM templates are a performance win, but they create a cache invalidation problem. Automate the rebuild trigger so templates stay in sync with the codebase.

---

## What I Would Do Differently

### 1. Start with Remote Terraform State
Local Terraform state works for a single developer but is fundamentally broken for teams. I would set up an S3 backend with state locking from day one, even for a POC. The cost is near-zero and it prevents state corruption.

### 2. Use the Terraform Proxmox Provider
I used Ansible's `command` module to call `qm` CLI commands on Proxmox. This works but means Terraform has no awareness of VMs inside Proxmox. The `bpg/proxmox` Terraform provider would give state tracking, drift detection, and `terraform plan` visibility. I chose Ansible because I was more productive with it under time pressure, but the Terraform provider is the better long-term choice.

### 3. Add Log Collection from the Start
I built the pipeline as: spin up → deploy → smoke test → done. The case study explicitly asks to "collect and store logs and test results." I should have added `actions/upload-artifact` and VM log collection from the first iteration instead of treating it as an afterthought.

### 4. Document AI Interactions in Real Time
I captured decisions and stages in `implementation.md` but didn't log specific AI prompts and responses as I went. Reconstructing this after the fact (in `process.md`) is less authentic than capturing it live. For the next project, I would keep a running log of interesting AI interactions as they happen.

---

## What Surprised Me

### 1. AI Quality on Ansible Playbooks
The AI-generated Ansible playbooks were production-quality on the first pass for straightforward tasks (app deploy, VM destroy). The module names, parameter formats, and YAML structure were consistently correct. Where AI struggled was with Proxmox-specific operations — `qm` CLI flags, disk import sequences, and cloud-init configuration are niche enough that the AI needed multiple iterations.

### 2. How Much Time Debugging SSH Saves Later
The SSH proxy chain took ~2 hours to get right. But once it worked, every subsequent stage (template creation, VM provisioning, app deployment, cleanup) "just worked" because they all share the same SSH config. The investment in the SSH foundation had a 10x payoff.

### 3. Preview Environments Are More Useful Than I Expected
The case study asks for a pipeline that spins up, tests, and tears down a VM. I went beyond the ask and kept branch VMs alive as preview environments. This turned out to be genuinely useful during development — I could SSH into a branch VM, inspect its state, and debug issues without re-running the full pipeline.

### 4. The "Future Plan" Exercise Was Valuable
Writing the production hardening plan (Security, Cost, Monitoring, Operational Excellence, Architecture) forced me to think critically about every shortcut in the POC. Several items I documented as "future work" (like job timeouts) were quick enough to implement immediately, so I went back and added them.

---

## Growth

### Technical Skills Gained
- **Proxmox VE** — First time managing a hypervisor programmatically. Now comfortable with `qm` CLI, cloud-init, and VM templates.
- **Hetzner Cloud** — First time using Hetzner. The Terraform provider is clean and well-documented. Private networks + firewalls are straightforward.
- **Ansible for VM lifecycle** — I've used Ansible for config management before, but not for VM creation/destruction on a hypervisor. The `command` module with `qm` is powerful but fragile — I'd use a dedicated Proxmox Ansible collection or Terraform provider next time.

### Process Skills Reinforced
- **Idempotency discipline** — Every playbook task must be safe to run twice. This is easy to say and hard to do consistently. The golden template creation playbook went through 3 iterations to become truly idempotent.
- **Pipeline thinking** — Serialisation, failure handling, cleanup, and artifact collection are not afterthoughts — they are core pipeline features.
- **Knowing when to stop** — A POC that demonstrates competence is more valuable than a half-finished production system. The Future Plan section bridges the gap by showing I know what production would require.

---

> This reflection was produced as part of the MILES DevOps Case Study to document lessons learned and personal growth.
