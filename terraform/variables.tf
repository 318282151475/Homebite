# terraform/variables.tf

# ─────────────────────────────────────────
# AWS SETTINGS
# ─────────────────────────────────────────

variable "aws_region" {
  description = "AWS region to deploy HomeBite"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Project name used for naming all resources"
  type        = string
  default     = "homebite"
}

# ─────────────────────────────────────────
# EC2 SETTINGS
# ─────────────────────────────────────────

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "ami_id" {
  description = "Ubuntu 26.04 LTS AMI ID for ap-south-1 (Mumbai)"
  type        = string
  default     = "ami-07a00cf47dbbc844c"
}

variable "key_name" {
  description = "Name of SSH key pair to access EC2"
  type        = string
  default     = "homebite-key"
}

variable "public_key_path" {
  description = "Path to your SSH public key on local machine"
  type        = string
  default     = "~/.ssh/homebite_key.pub"
}

# ─────────────────────────────────────────
# RDS SETTINGS
# ─────────────────────────────────────────

variable "db_instance_class" {
  description = "RDS instance type"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "Initial database name on RDS"
  type        = string
  default     = "homebite"
}

variable "db_username" {
  description = "RDS master username"
  type        = string
  default     = "admin"
}

variable "db_password" {
  description = "RDS master password — passed via tfvars, never hardcoded"
  type        = string
  sensitive   = true
}

# ─────────────────────────────────────────
# NETWORKING
# ─────────────────────────────────────────

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR for public subnet (EC2 lives here)"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_cidr" {
  description = "CIDR for private subnet (RDS lives here)"
  type        = string
  default     = "10.0.2.0/24"
}

variable "private_subnet_cidr_2" {
  description = "Second private subnet (RDS requires 2 AZs)"
  type        = string
  default     = "10.0.3.0/24"
}