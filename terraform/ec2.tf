# terraform/ec2.tf

# ─────────────────────────────────────────
# KEY PAIR
# SSH key to access EC2 securely
# ─────────────────────────────────────────

resource "aws_key_pair" "homebite" {
  key_name   = var.key_name
  public_key = file(var.public_key_path)

  tags = {
    Name    = "${var.project_name}-key"
    Project = var.project_name
  }
}

# ─────────────────────────────────────────
# EC2 INSTANCE
# Runs all HomeBite Docker containers
# ─────────────────────────────────────────

resource "aws_instance" "homebite" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.ec2.id]
  key_name               = aws_key_pair.homebite.key_name

  # Increase root volume to 20GB
  # Default 8GB fills up quickly with Docker images
  root_block_device {
    volume_size = 20
    volume_type = "gp2"
  }

  # ── USER DATA ──────────────────────────
  # Runs automatically on first boot
  # Installs Docker, Docker Compose, Git
  # ──────────────────────────────────────
  user_data = <<-EOF
    #!/bin/bash
    set -e

    echo "=== HomeBite EC2 Setup Starting ==="

    # Update package list
    apt-get update -y

    # Install required packages
    apt-get install -y \
      docker.io \
      docker-compose \
      git \
      mysql-client \
      curl \
      wget

    # Start Docker service
    systemctl start docker
    systemctl enable docker

    # Add ubuntu user to docker group
    # So ubuntu user can run docker without sudo
    usermod -aG docker ubuntu

    # Verify installations
    docker --version
    docker-compose --version
    git --version
    mysql --version

    echo "=== HomeBite EC2 Setup Complete ==="
  EOF

  tags = {
    Name    = "${var.project_name}-server"
    Project = var.project_name
  }
}