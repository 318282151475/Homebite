# terraform/security.tf

# ─────────────────────────────────────────
# EC2 SECURITY GROUP
# Controls traffic to/from your EC2 instance
# ─────────────────────────────────────────

resource "aws_security_group" "ec2" {
  name        = "${var.project_name}-ec2-sg"
  description = "Security group for HomeBite EC2 instance"
  vpc_id      = aws_vpc.main.id

  # ── INBOUND RULES ──────────────────────

  # SSH — only for you to log in and manage server
  ingress {
    description = "SSH access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP — users access HomeBite frontend
  ingress {
    description = "HTTP access for HomeBite app"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # ── OUTBOUND RULES ─────────────────────

  # Allow all outbound traffic
  # EC2 needs to:
  # → Pull from GitHub (git clone)
  # → Pull Docker images
  # → Talk to RDS (in private subnet)
  # → Talk to AWS services
  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${var.project_name}-ec2-sg"
    Project = var.project_name
  }
}

# ─────────────────────────────────────────
# RDS SECURITY GROUP
# Controls traffic to/from your RDS MySQL
# ─────────────────────────────────────────

resource "aws_security_group" "rds" {
  name        = "${var.project_name}-rds-sg"
  description = "Security group for HomeBite RDS MySQL"
  vpc_id      = aws_vpc.main.id

  # ── INBOUND RULES ──────────────────────

  # MySQL — ONLY from EC2 security group
  # Nobody else can reach the database
  ingress {
    description     = "MySQL access from EC2 only"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2.id]
  }

  # ── OUTBOUND RULES ─────────────────────

  # Allow all outbound
  # RDS needs to respond to queries
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${var.project_name}-rds-sg"
    Project = var.project_name
  }
}