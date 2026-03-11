# Terraform configuration for Hetzner and Proxmox

## Overview
This directory contains Terraform code to provision a Hetzner server and prepare it for Proxmox VE installation.

## Steps
1. Configure Hetzner Cloud provider
2. Define resources for server, network, and firewall
3. Output server details for Proxmox setup

---

## Files
- `main.tf`: Main Terraform configuration
- `variables.tf`: Input variables
- `outputs.tf`: Output values
- `README.md`: Documentation

---

## Usage
1. Set Hetzner API token in environment or `terraform.tfvars`
2. Run `terraform init`
3. Run `terraform apply`
4. Use output to access server and install Proxmox
