# terraform/outputs.tf

# ─────────────────────────────────────────
# EC2 OUTPUTS
# ─────────────────────────────────────────

output "ec2_public_ip" {
  description = "Public IP of HomeBite EC2 instance"
  value       = aws_instance.homebite.public_ip
}

output "ec2_instance_id" {
  description = "EC2 instance ID — use to stop/start instance"
  value       = aws_instance.homebite.id
}

output "ssh_command" {
  description = "Ready-to-use SSH command to connect to EC2"
  value       = "ssh -i ~/.ssh/homebite_key ubuntu@${aws_instance.homebite.public_ip}"
}

# ─────────────────────────────────────────
# RDS OUTPUTS
# ─────────────────────────────────────────

output "rds_endpoint" {
  description = "RDS endpoint — use as DB_HOST in .env.aws"
  value       = aws_db_instance.mysql.endpoint
}

output "rds_port" {
  description = "RDS port"
  value       = aws_db_instance.mysql.port
}

output "rds_identifier" {
  description = "RDS identifier — use to stop/start RDS"
  value       = aws_db_instance.mysql.identifier
}

# ─────────────────────────────────────────
# NETWORK OUTPUTS
# ─────────────────────────────────────────

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "Public subnet ID"
  value       = aws_subnet.public.id
}

# ─────────────────────────────────────────
# HELPFUL NEXT STEPS
# ─────────────────────────────────────────

output "next_steps" {
  description = "What to do after terraform apply"
  value       = <<-EOT

    ===== HomeBite AWS Deployment =====

    1. SSH into EC2:
       ssh -i ~/.ssh/homebite_key ubuntu@${aws_instance.homebite.public_ip}

    2. On EC2 — clone repo:
       git clone https://github.com/318282151475/Homebite.git
       cd Homebite
       git checkout aws

    3. Run deploy script:
       bash deploy.sh

    4. Init databases on RDS:
       mysql -h ${aws_db_instance.mysql.endpoint} -u admin -p < infra/mysql/init_user_db.sql
       mysql -h ${aws_db_instance.mysql.endpoint} -u admin -p < infra/mysql/init_chef_db.sql
       mysql -h ${aws_db_instance.mysql.endpoint} -u admin -p < infra/mysql/init_order_db.sql
       mysql -h ${aws_db_instance.mysql.endpoint} -u admin -p < infra/mysql/init_delivery_db.sql
       mysql -h ${aws_db_instance.mysql.endpoint} -u admin -p < infra/mysql/init_logging_db.sql
       mysql -h ${aws_db_instance.mysql.endpoint} -u admin -p < infra/mysql/init_grants.sql

    5. Start HomeBite:
       docker-compose -f docker-compose.aws.yml up --build -d

    6. Access HomeBite:
       http://${aws_instance.homebite.public_ip}

    7. Stop EC2 when done (saves money):
       aws ec2 stop-instances --instance-ids ${aws_instance.homebite.id}

    8. Stop RDS when done (saves money):
       aws rds stop-db-instance --db-instance-identifier ${aws_db_instance.mysql.identifier}

    ====================================
  EOT
}