variable "hcloud_token" {
  description = "Hetzner Cloud API token"
  type        = string
}

variable "server_type" {
  description = "Hetzner server type for Proxmox (e.g., cx21, cpx31)"
  type        = string
  default     = "cpx31"
}

variable "bastion_server_type" {
  description = "Hetzner server type for bastion host (small is sufficient)"
  type        = string
  default     = "cx22"
}

variable "server_image" {
  description = "OS image for servers (e.g., ubuntu-22.04)"
  type        = string
  default     = "ubuntu-22.04"
}

variable "server_location" {
  description = "Hetzner location (e.g., fsn1, nbg1, hel1)"
  type        = string
  default     = "fsn1"
}

variable "ssh_key_name" {
  description = "Name of SSH key in Hetzner Cloud"
  type        = string
}
