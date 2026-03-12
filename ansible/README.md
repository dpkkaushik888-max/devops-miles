---
# Ansible Playbooks for VM Template & App Deployment

## Structure
- `proxmox_setup.yml`: Prepare Proxmox VE and create VM template
- `app_deploy.yml`: Deploy Python web app and DB to VM
- `roles/`: Modular roles for template creation, app install, DB setup

## Steps
1. Prepare Proxmox VE (install packages, configure SSH, network)
2. Create minimal Ubuntu/Debian VM template (hardened, SSH keys, minimal packages)
3. Deploy Python app and backend DB to VM
4. Run smoke tests

## Usage
- Run playbooks with: `ansible-playbook proxmox_setup.yml` and `ansible-playbook app_deploy.yml`
- Inventory and variables files to be added for host details

---

> All playbook development and decisions will be logged in implementation.md
