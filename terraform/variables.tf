variable "hcloud_token" {
  description = "Hetzner Cloud API token"
  type        = string
}

variable "server_type" {
  description = "Hetzner server type (e.g., cx21, cpx31, etc.)"
  type        = string
  default     = "cpx31"
}

variable "server_image" {
  description = "OS image for server (e.g., ubuntu-22.04)"
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

variable "network_id" {
  description = "Hetzner network ID"
  type        = string
}
