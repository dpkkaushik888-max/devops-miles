output "server_ip" {
  description = "IPv4 address of the provisioned Hetzner server"
  value       = hcloud_server.proxmox.ipv4_address
}

output "server_id" {
  description = "ID of the provisioned Hetzner server"
  value       = hcloud_server.proxmox.id
}
