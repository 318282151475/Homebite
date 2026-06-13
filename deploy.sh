#!/bin/bash
# deploy.sh
# Run this on EC2 after cloning the repo
# Creates all .env.aws files with real AWS values

set -e

echo ""
echo "===== HomeBite AWS Deployment Setup ====="
echo ""

# ─────────────────────────────────────────
# STEP 1 — SWAP SPACE
# Kafka needs ~600MB — t3.micro has 1GB total
# ─────────────────────────────────────────

echo "Setting up swap space (needed for Kafka)..."
if [ ! -f /swapfile ]; then
  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
  echo "✅ Swap configured (2GB)"
else
  echo "✅ Swap already exists — skipping"
fi

echo ""

# ─────────────────────────────────────────
# STEP 2 — COLLECT VALUES FROM USER
# ─────────────────────────────────────────

echo "Enter RDS endpoint (from terraform output):"
echo "Example: homebite-db.xxxxx.ap-south-1.rds.amazonaws.com"
read -r RDS_ENDPOINT

echo ""
echo "Enter RDS password (same as terraform.tfvars):"
read -rs RDS_PASSWORD
echo ""

echo ""
echo "Enter JWT secret key:"
echo "Generate one with: python3 -c \"import secrets; print(secrets.token_hex(32))\""
read -r JWT_SECRET

echo ""
echo "Creating .env.aws files..."
echo ""

# ─────────────────────────────────────────
# USER SERVICE
# ─────────────────────────────────────────

cat > services/user_service/.env.aws << EOF
APP_ENV=production
APP_NAME=user_service
APP_PORT=8001
DEBUG=false

DB_HOST=${RDS_ENDPOINT}
DB_PORT=3306
DB_NAME=user_db
DB_USER=admin
DB_PASSWORD=${RDS_PASSWORD}

JWT_SECRET_KEY=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC_USER_REGISTERED=user.registered
EOF

echo "✅ user_service/.env.aws created"

# ─────────────────────────────────────────
# CHEF SERVICE
# ─────────────────────────────────────────

cat > services/chef_service/.env.aws << EOF
APP_ENV=production
APP_NAME=chef_service
APP_PORT=8002
DEBUG=false

DB_HOST=${RDS_ENDPOINT}
DB_PORT=3306
DB_NAME=chef_db
DB_USER=admin
DB_PASSWORD=${RDS_PASSWORD}

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=1

KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC_ORDER_CREATED=order.created
KAFKA_TOPIC_CHEF_ASSIGNED=chef.assigned
KAFKA_CONSUMER_GROUP=chef-service-group
EOF

echo "✅ chef_service/.env.aws created"

# ─────────────────────────────────────────
# ORDER SERVICE
# ─────────────────────────────────────────

cat > services/order_service/.env.aws << EOF
APP_ENV=production
APP_NAME=order_service
APP_PORT=8003
DEBUG=false

DB_HOST=${RDS_ENDPOINT}
DB_PORT=3306
DB_NAME=order_db
DB_USER=admin
DB_PASSWORD=${RDS_PASSWORD}

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=2

KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC_ORDER_CREATED=order.created
KAFKA_TOPIC_CHEF_ASSIGNED=chef.assigned
KAFKA_TOPIC_DELIVERY_STARTED=delivery.started
KAFKA_TOPIC_DELIVERY_COMPLETED=delivery.completed
KAFKA_CONSUMER_GROUP=order-service-group
EOF

echo "✅ order_service/.env.aws created"

# ─────────────────────────────────────────
# DELIVERY SERVICE
# ─────────────────────────────────────────

cat > services/delivery_service/.env.aws << EOF
APP_ENV=production
APP_NAME=delivery_service
APP_PORT=8004
DEBUG=false

DB_HOST=${RDS_ENDPOINT}
DB_PORT=3306
DB_NAME=delivery_db
DB_USER=admin
DB_PASSWORD=${RDS_PASSWORD}

KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC_CHEF_ASSIGNED=chef.assigned
KAFKA_TOPIC_DELIVERY_STARTED=delivery.started
KAFKA_TOPIC_DELIVERY_COMPLETED=delivery.completed
KAFKA_CONSUMER_GROUP=delivery-service-group
EOF

echo "✅ delivery_service/.env.aws created"

# ─────────────────────────────────────────
# LOGGING SERVICE
# ─────────────────────────────────────────

cat > services/logging_service/.env.aws << EOF
APP_ENV=production
APP_NAME=logging_service
APP_PORT=8006
DEBUG=false

DB_HOST=${RDS_ENDPOINT}
DB_PORT=3306
DB_NAME=logging_db
DB_USER=admin
DB_PASSWORD=${RDS_PASSWORD}

KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC_USER_REGISTERED=user.registered
KAFKA_TOPIC_ORDER_CREATED=order.created
KAFKA_TOPIC_CHEF_ASSIGNED=chef.assigned
KAFKA_TOPIC_DELIVERY_STARTED=delivery.started
KAFKA_TOPIC_DELIVERY_COMPLETED=delivery.completed
KAFKA_CONSUMER_GROUP=logging-service-group
EOF

echo "✅ logging_service/.env.aws created"

# ─────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────

echo ""
echo "===== All .env.aws files created! ====="
echo ""
echo "Next steps:"
echo ""
echo "1. Init databases on RDS:"
echo "   mysql -h ${RDS_ENDPOINT} -u admin -p < infra/mysql/init_user_db.sql"
echo "   mysql -h ${RDS_ENDPOINT} -u admin -p < infra/mysql/init_chef_db.sql"
echo "   mysql -h ${RDS_ENDPOINT} -u admin -p < infra/mysql/init_order_db.sql"
echo "   mysql -h ${RDS_ENDPOINT} -u admin -p < infra/mysql/init_delivery_db.sql"
echo "   mysql -h ${RDS_ENDPOINT} -u admin -p < infra/mysql/init_logging_db.sql"
echo "   mysql -h ${RDS_ENDPOINT} -u admin -p < infra/mysql/init_grants.sql"
echo ""
echo "2. Start HomeBite:"
echo "   docker-compose -f docker-compose.aws.yml up --build -d"
echo ""
echo "3. Access HomeBite:"
echo "   http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo ""
echo "======================================="