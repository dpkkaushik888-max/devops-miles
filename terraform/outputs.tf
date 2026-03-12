output "bastion_public_ip" {
  description = "Public IPv4 address of the bastion host"
  value       = hcloud_server.bastion.ipv4_address
}

output "bastion_private_ip" {
  description = "Private IPv4 address of the bastion host"
  value       = hcloud_server_network.bastion_network.ip
}

output "proxmox_private_ip" {
  description = "Private IPv4 address of the Proxmox server"
  value       = hcloud_server_network.proxmox_network.ip
}

output "server_id" {
  description = "ID of the Proxmox server"
  value       = hcloud_server.proxmox.id
}

output "ssh_command" {
  description = "SSH jump command to access Proxmox via bastion"
  value       = "ssh -A -J root@${hcloud_server.bastion.ipv4_address} root@${hcloud_server_network.proxmox_network.ip}"
}
