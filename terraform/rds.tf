# terraform/rds.tf

# ─────────────────────────────────────────
# RDS MYSQL INSTANCE
# Managed MySQL database for HomeBite
# Lives in private subnet — not accessible
# from internet, only from EC2
# ─────────────────────────────────────────

resource "aws_db_instance" "mysql" {
  # ── IDENTITY ───────────────────────────
  identifier = "${var.project_name}-db"

  # ── ENGINE ─────────────────────────────
  engine         = "mysql"
  engine_version = "8.0"

  # ── SIZE ───────────────────────────────
  instance_class    = var.db_instance_class
  allocated_storage = 20
  storage_type      = "gp2"

  # ── CREDENTIALS ────────────────────────
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  # ── NETWORK ────────────────────────────
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  # ── BACKUP ─────────────────────────────
  backup_retention_period = 0
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  # ── PERFORMANCE ────────────────────────
  performance_insights_enabled = false

  # ── LIFECYCLE ──────────────────────────
  skip_final_snapshot       = true
  delete_automated_backups  = true

  # ── MONITORING ─────────────────────────
  monitoring_interval = 0

  tags = {
    Name    = "${var.project_name}-db"
    Project = var.project_name
  }
}