terraform {
  required_providers {
    hcloud = {
      source = "hetznercloud/hcloud"
      version = ">= 1.43.0"
    }
  }
}

provider "hcloud" {
  token = var.hcloud_token
}

resource "hcloud_server" "proxmox" {
  name        = "proxmox-server"
  server_type = var.server_type
  image       = var.server_image
  location    = var.server_location
  ssh_keys    = [var.ssh_key_name]
}

resource "hcloud_firewall" "proxmox_fw" {
  name = "proxmox-firewall"
  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "22"
    source_ips = ["0.0.0.0/0"]
  }
}

resource "hcloud_server_network" "proxmox_network" {
  server_id = hcloud_server.proxmox.id
  network_id = var.network_id
}

output "server_ip" {
  value = hcloud_server.proxmox.ipv4_address
}
