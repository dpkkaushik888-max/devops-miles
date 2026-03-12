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

# Private network for internal communication
resource "hcloud_network" "private_net" {
  name     = "private-network"
  ip_range = "10.2.0.0/16"
}

resource "hcloud_network_subnet" "private_subnet" {
  network_id   = hcloud_network.private_net.id
  type         = "cloud"
  network_zone = "eu-central"
  ip_range     = "10.2.0.0/24"
}

# Bastion host - public entry point for SSH access
resource "hcloud_server" "bastion" {
  name        = "bastion-host"
  server_type = var.bastion_server_type
  image       = var.server_image
  location    = var.server_location
  ssh_keys    = [var.ssh_key_name]

  public_net {
    ipv4_enabled = true
    ipv6_enabled = false
  }
}

resource "hcloud_server_network" "bastion_network" {
  server_id  = hcloud_server.bastion.id
  network_id = hcloud_network.private_net.id
  ip         = "10.2.0.3"
}

resource "hcloud_firewall" "bastion_fw" {
  name = "bastion-firewall"
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "22"
    source_ips = ["0.0.0.0/0"]
  }
}

resource "hcloud_firewall_attachment" "bastion_fw_attach" {
  firewall_id = hcloud_firewall.bastion_fw.id
  server_ids  = [hcloud_server.bastion.id]
}

# Proxmox server - private, accessible only via bastion
resource "hcloud_server" "proxmox" {
  name        = "Proxmox-vm-01"
  server_type = var.server_type
  image       = var.server_image
  location    = var.server_location
  ssh_keys    = [var.ssh_key_name]

  public_net {
    ipv4_enabled = false
    ipv6_enabled = false
  }
}

resource "hcloud_server_network" "proxmox_network" {
  server_id  = hcloud_server.proxmox.id
  network_id = hcloud_network.private_net.id
  ip         = "10.2.0.2"
}

resource "hcloud_firewall" "proxmox_fw" {
  name = "proxmox-firewall"
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "22"
    source_ips = ["10.2.0.3/32"]
  }
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "8006"
    source_ips = ["10.2.0.3/32"]
  }
}

resource "hcloud_firewall_attachment" "proxmox_fw_attach" {
  firewall_id = hcloud_firewall.proxmox_fw.id
  server_ids  = [hcloud_server.proxmox.id]
}

# Route all internet traffic from private network through bastion
resource "hcloud_network_route" "internet_route" {
  network_id  = hcloud_network.private_net.id
  destination = "0.0.0.0/0"
  gateway     = "10.2.0.3"
}
