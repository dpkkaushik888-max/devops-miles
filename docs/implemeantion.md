# Implementation Log

This file tracks all steps, decisions, and progress for the DevOps MILES challenge implementation.

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
- Created ansible/README.md, proxmox_setup.yml, app_deploy.yml
- Playbooks cover Proxmox setup, VM template creation, app deployment, DB setup, and smoke tests
- Status: In Progress

## Stage 4: Python Web App
- Created app/README.md, app.py, migrate.py, requirements.txt
- Flask app with SQLite backend: takes name, stores in DB, returns greeting
- Status: Completed

---

## Next Steps
- Complete Terraform setup
- Create Ansible playbooks for VM template and app deployment
- Develop Python web app
- Configure GitHub Actions pipeline
- Test pipeline
- Document process and reflections

---

> All stages will be logged here with timestamps, decisions, and git commit references.
