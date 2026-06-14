# 🍽️ HomeBite — Home Chef Food Delivery Platform

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=flat&logo=docker&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=flat&logo=kubernetes&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-232F3E?style=flat&logo=amazonaws&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=flat&logo=terraform&logoColor=white)
![Kafka](https://img.shields.io/badge/Apache_Kafka-231F20?style=flat&logo=apache-kafka&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat&logo=mysql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7.2-DC382D?style=flat&logo=redis&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=flat&logo=prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-F46800?style=flat&logo=grafana&logoColor=white)

A **production-grade microservices food delivery platform** connecting customers with home chefs. Built with event-driven architecture, supporting three deployment models — local Docker Compose, Kubernetes, and AWS EC2 with Terraform.

---

## 📋 Table of Contents

- [What Is HomeBite](#what-is-homebite)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Services](#services)
- [Event Flow](#event-flow)
- [Deployment Models](#deployment-models)
  - [Local — Docker Compose](#1-local--docker-compose)
  - [Local AWS Structure Test](#2-local-aws-structure-test)
  - [AWS EC2 — Terraform + Docker Compose](#3-aws-ec2--terraform--docker-compose)
  - [Kubernetes](#4-kubernetes)
- [Security Design](#security-design)
- [Observability](#observability)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Key Engineering Decisions](#key-engineering-decisions)
- [Problems Encountered and Solved](#problems-encountered-and-solved)

---

## What Is HomeBite

HomeBite is a home-cooked food delivery platform. Unlike restaurant-based delivery apps, HomeBite connects customers directly with verified home chefs in their city.

**User Roles:**
- **Customer** — browses chefs, places orders, tracks delivery
- **Chef** — receives orders, marks food ready for pickup
- **Delivery Person** — accepts available deliveries, updates status
- **Admin** — creates delivery person accounts

**Order Lifecycle:**
```
Customer places order
        ↓
Chef gets assigned automatically (or by customer choice)
        ↓
Chef prepares food → marks ready
        ↓
Delivery person accepts → picks up → delivers
        ↓
Order marked delivered → Chef becomes available again
```

---

## Architecture

```
                         Internet
                            │
                     ┌──────▼───────┐
                     │     Nginx     │  ← Single entry point
                     │  (Auth + Proxy)│  ← JWT validation via auth_request
                     └──────┬───────┘  ← Rate limiting
                            │
          ┌─────────────────┼─────────────────────┐
          │                 │                     │
    ┌─────▼─────┐   ┌───────▼──────┐   ┌─────────▼────────┐
    │user_service│   │ chef_service │   │  order_service   │
    │  :8001    │   │    :8002     │   │     :8003        │
    └─────┬─────┘   └───────┬──────┘   └─────────┬────────┘
          │                 │                     │
    ┌─────▼─────┐                       ┌─────────▼────────┐
    │delivery   │                       │  logging_service  │
    │_service   │                       │     :8006        │
    │  :8004    │                       └──────────────────┘
    └───────────┘
          │
          └────────┬────────┘
                   │
            ┌──────▼──────┐
            │    Kafka     │  ← Async event bus
            │  (5 topics)  │
            └──────┬──────┘
                   │
         ┌─────────┼─────────┐
         │         │         │
    ┌────▼───┐ ┌───▼───┐ ┌──▼────┐
    │ MySQL  │ │ Redis │ │  ZK   │
    │(per db)│ │(JWT)  │ │(Kafka)│
    └────────┘ └───────┘ └───────┘
```

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| API Framework | FastAPI + Python 3.12 | Async, fast, auto Swagger docs |
| Database | MySQL 8.0 (per service) | Each service owns its data |
| Message Broker | Apache Kafka | Async decoupled communication |
| Cache / Auth | Redis 7.2 | JWT token blacklist |
| Reverse Proxy | Nginx 1.25 | Auth, routing, rate limiting |
| Containerization | Docker + Docker Compose | All deployment models |
| Orchestration | Kubernetes | Production K8s deployment |
| Cloud | AWS (EC2, RDS, S3, VPC, IAM) | Cloud deployment |
| IaC | Terraform | AWS infrastructure provisioning |
| Metrics | Prometheus + Grafana | Observability (local/K8s) |
| ORM | SQLAlchemy (async) | Non-blocking DB queries |
| Kafka Client | aiokafka | Async Kafka producer/consumer |

---

## Services

### user_service (port 8001)
- JWT authentication (access + refresh tokens)
- User registration with role selection (customer/chef/delivery_person)
- Token blacklist via Redis (logout)
- Timing-attack resistant password verification
- Internal token verification endpoint for Nginx auth_request

### chef_service (port 8002)
- Chef profile management
- Kafka consumer for `order.created` events
- Auto-assigns best available chef by rating
- Respects customer's chef selection
- Publishes `chef.assigned` event

### order_service (port 8003)
- Order lifecycle management
- Kafka producer for `order.created`
- Kafka consumer for `chef.assigned`, `delivery.started`, `delivery.completed`
- Status transitions: pending → chef_assigned → preparing → ready_for_pickup → out_for_delivery → delivered

### delivery_service (port 8004)
- Delivery record management
- Self-assign flow for delivery persons
- Publishes `delivery.started` and `delivery.completed` events
- Idempotent accept endpoint (prevents double assignment)

### notification_service (port 8005)
- Stateless Kafka consumer
- Consumes all events
- Email notification (future feature)

### logging_service (port 8006)
- Audit trail for all system events
- Consumes all Kafka topics
- Stores structured logs to MySQL

---

## Event Flow

```
Kafka Topics:
- user.registered
- order.created
- chef.assigned
- delivery.started
- delivery.completed

Flow:
1. Customer places order
   → order_service publishes order.created

2. chef_service consumes order.created
   → assigns chef (customer choice or best available)
   → publishes chef.assigned

3. order_service consumes chef.assigned
   → updates order status to chef_assigned

4. delivery_service consumes chef.assigned
   → creates delivery record
   → delivery person can see and accept

5. delivery_service.status = PICKED_UP
   → publishes delivery.started
   → order_service updates to out_for_delivery

6. delivery_service.status = DELIVERED
   → publishes delivery.completed
   → order_service updates to delivered

All events → logging_service (audit trail)
All events → notification_service (future: email notifications)
```

---

## Deployment Models

HomeBite supports three deployment models. Each is fully independent — no code changes needed to switch between them.

---

### 1. Local — Docker Compose

Runs everything locally including MySQL, Kafka, Redis, Prometheus and Grafana.

**Branch:** `main`

#### Prerequisites
- Docker Desktop

#### Quick Start

```bash
# Clone repository
git clone https://github.com/318282151475/Homebite.git
cd Homebite

# Switch to main branch
git checkout main

# Copy environment files
cp services/user_service/.env.example services/user_service/.env
cp services/chef_service/.env.example services/chef_service/.env
cp services/order_service/.env.example services/order_service/.env
cp services/delivery_service/.env.example services/delivery_service/.env
cp services/notification_service/.env.example services/notification_service/.env
cp services/logging_service/.env.example services/logging_service/.env

# Start all services
docker compose up -d

# Watch logs
docker compose logs -f
```

#### Access Points
```
Frontend      → http://localhost
phpMyAdmin    → http://localhost:8080
Prometheus    → http://localhost:9200
Grafana       → http://localhost:3000  (admin/admin123)
```

#### Development Mode (Hot Reload)
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

---

### 2. Local AWS Structure Test

Tests the exact AWS deployment structure locally before deploying to AWS.
Replaces MySQL container with admin user (mirrors RDS behaviour).
Removes Prometheus, Grafana, phpMyAdmin to mirror AWS compose file.

**Branch:** `aws`

#### Prerequisites
- Docker Desktop
- Stop any local MySQL service (frees port 3306)

#### Quick Start

```bash
# Switch to aws branch
git checkout aws

# Create .env.test files for each service
# (copy from .env.example and update DB_USER=admin, DB_PASSWORD=testpassword)

# Start AWS structure test
docker-compose -f docker-compose.test.yml up --build

# Verify all containers healthy
docker-compose -f docker-compose.test.yml ps -a
```

#### Expected Output
```
homebite_mysql_test       Up (healthy)
homebite_redis            Up (healthy)
homebite_zookeeper        Up (healthy)
homebite_kafka            Up (healthy)
homebite_kafka_init       Exited (0)    ← normal
homebite_user_service     Up (healthy)
homebite_chef_service     Up (healthy)
homebite_order_service    Up (healthy)
homebite_delivery_service Up (healthy)
homebite_logging_service  Up (healthy)
homebite_nginx            Up
```

#### Access Points
```
Frontend  → http://localhost
```

---

### 3. AWS EC2 — Terraform + Docker Compose

Deploys HomeBite on AWS using:
- **EC2 t3.macro** — runs all Docker containers
- **RDS MySQL** — managed database (replaces MySQL container)
- **VPC** — private network with public/private subnets
- **Terraform** — provisions all infrastructure as code

**Branch:** `aws`

#### Prerequisites
- AWS account with IAM user
- AWS CLI configured (`aws configure`)
- Terraform installed
- SSH key pair generated

#### Step 1 — Provision Infrastructure

```bash
cd terraform/

# Initialise Terraform
terraform init

# Preview what will be created
terraform plan

# Create AWS infrastructure (~5-10 minutes)
terraform apply
```

After apply completes, note the outputs:
```
ec2_public_ip = "13.235.x.x"
rds_endpoint  = "homebite-db.xxxxx.ap-south-1.rds.amazonaws.com:3306"
```

#### Step 2 — SSH Into EC2

```bash
ssh -i ~/.ssh/homebite_key ubuntu@<EC2_IP>
```

#### Step 3 — Setup on EC2

```bash
# Clone repository
git clone https://github.com/318282151475/Homebite.git
cd Homebite
git checkout aws

# Run deploy script (creates all .env.aws files)
bash deploy.sh
# Enter RDS endpoint when prompted
# Enter RDS password when prompted
# Enter JWT secret key when prompted

# Initialise databases on RDS
mysql -h <RDS_ENDPOINT> -u admin -p < infra/mysql/init_user_db.sql
mysql -h <RDS_ENDPOINT> -u admin -p < infra/mysql/init_chef_db.sql
mysql -h <RDS_ENDPOINT> -u admin -p < infra/mysql/init_order_db.sql
mysql -h <RDS_ENDPOINT> -u admin -p < infra/mysql/init_delivery_db.sql
mysql -h <RDS_ENDPOINT> -u admin -p < infra/mysql/init_logging_db.sql
mysql -h <RDS_ENDPOINT> -u admin -p < infra/mysql/init_grants.sql
```

#### Step 4 — Deploy HomeBite

```bash
docker-compose -f docker-compose.aws.yml up --build -d

# Watch startup
docker-compose -f docker-compose.aws.yml logs -f
```

#### Step 5 — Access

```
Frontend  → http://<EC2_IP>
```

#### Stop EC2 When Not Using (saves money)

```bash
aws ec2 stop-instances --instance-ids <instance-id>

# Start again when needed
aws ec2 start-instances --instance-ids <instance-id>
```

#### Destroy Everything When Done

```bash
# On your local machine
cd terraform/
terraform destroy
```

#### AWS Infrastructure Created

```
VPC (10.0.0.0/16)
├── Public Subnet  → EC2 t3.macro(Docker + all services)
├── Private Subnet → RDS MySQL db.t3.micro
├── Internet Gateway
├── Route Tables
├── Security Groups (EC2: 22/80, RDS: 3306 from EC2 only)
└── Key Pair
```

#### What Changes Between Local and AWS

| Component | Local | AWS |
|-----------|-------|-----|
| MySQL | Docker container | AWS RDS (managed) |
| DB user | root | admin |
| DB host | mysql (Docker DNS) | RDS endpoint (real DNS) |
| Prometheus | Running | Removed (saves RAM) |
| Grafana | Running | Removed (saves RAM) |
| phpMyAdmin | Running | Removed (saves RAM) |
| Nginx DNS resolver | 127.0.0.11 | 127.0.0.11 (same) |
| App code | Unchanged | Unchanged |

---

### 4. Kubernetes

Deploys HomeBite on Kubernetes (local Docker Desktop or AWS EKS).

**Branch:** `main`

#### Prerequisites
- Docker Desktop with Kubernetes enabled
- kubectl
- Images pushed to Docker Hub

#### Deploy

```bash
# Switch to main branch
git checkout main

# 1. Namespaces
kubectl apply -f k8s/namespaces/

# 2. Storage
kubectl apply -f k8s/storage/

# 3. Config and Secrets
kubectl apply -f k8s/configmaps/
kubectl apply -f k8s/secrets/

# 4. Services (must be before pods — creates DNS entries)
kubectl apply -f k8s/services/infrastructure-services.yaml

# 5. Infrastructure
kubectl apply -f k8s/infrastructure/mysql-deployment.yaml
kubectl apply -f k8s/infrastructure/redis-deployment.yaml
kubectl apply -f k8s/infrastructure/zookeeper-deployment.yaml
kubectl apply -f k8s/infrastructure/kafka-deployment.yaml
kubectl apply -f k8s/infrastructure/kafka-init-job.yaml

# 6. App services
kubectl apply -f k8s/deployments/

# 7. Monitoring
kubectl apply -f k8s/monitoring/

# 8. Remaining services + ingress
kubectl apply -f k8s/services/
kubectl apply -f k8s/ingress/
```

#### Access via Port-Forward

```bash
kubectl port-forward service/nginx-service 8080:80 -n homebite
kubectl port-forward service/prometheus 9090:9090 -n monitoring
kubectl port-forward service/grafana 3000:3000 -n monitoring
```

```
Frontend      → http://localhost:8080
Prometheus    → http://localhost:9090
Grafana       → http://localhost:3000
```

---

## Security Design

### JWT Authentication
```
Login → access_token (30 min) + refresh_token (7 days)
Logout → token added to Redis blacklist with TTL
Every request → Nginx validates token via auth_request
```

### Nginx auth_request Pattern
```
Client Request
      ↓
Nginx receives request
      ↓
Nginx sends subrequest to user_service/internal/verify-token
      ↓
200 OK → forward request to upstream service
401    → return 401 to client (never reaches service)
```

### Why This Is Better Than Per-Service Auth
```
Without centralized auth:
→ Each service validates JWT independently
→ Duplicate code in 6 services
→ One service forgets validation = security hole

With Nginx auth_request:
→ Single validation point
→ No auth code in business services
→ Auth logic lives in user_service only
```

### Rate Limiting
```nginx
zone=api_limit   → 10 requests/second per IP
zone=auth_limit  → 5 requests/minute per IP (login/register)
```

---

## Observability

Available on **local** and **Kubernetes** deployments.

### Metrics (Prometheus + Grafana)

**Business Metrics:**
```
orders_placed_total
orders_in_progress
chefs_assigned_total
deliveries_completed_total
delivery_duration_minutes
```

**Auth Metrics:**
```
users_registered_total
login_attempts_total
token_blacklisted_total
```

**Kafka Metrics:**
```
kafka_events_published_total
kafka_events_consumed_total
```

### Grafana Dashboard
Pre-built dashboard with 5 sections:
- Business Metrics
- HTTP Traffic (requests/sec, error rate, P99 latency)
- Auth Metrics
- Kafka Events
- Service Health

---

## Project Structure

```
HomeBite/
├── services/
│   ├── user_service/
│   │   ├── app/
│   │   │   ├── api/v1/routes.py
│   │   │   ├── core/security.py
│   │   │   ├── crud/user.py
│   │   │   ├── kafka/consumer.py
│   │   │   ├── kafka/producer.py
│   │   │   ├── models/user.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── main.py
│   │   ├── .env.example
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── chef_service/        (same structure)
│   ├── order_service/       (same structure)
│   ├── delivery_service/    (same structure)
│   ├── notification_service/(same structure)
│   └── logging_service/     (same structure)
│
├── nginx/
│   ├── conf.d/
│   │   ├── homebite.conf    ← routing + auth + rate limiting
│   │   └── proxy_params.conf
│   ├── nginx.conf
│   └── Dockerfile
│
├── frontend/
│   └── index.html           ← Single page app (4 role dashboards)
│
├── k8s/                     ← Kubernetes manifests
│   ├── namespaces/
│   ├── infrastructure/
│   ├── deployments/
│   ├── monitoring/
│   ├── services/
│   └── ingress/
│
├── terraform/               ← AWS infrastructure as code
│   ├── main.tf
│   ├── variables.tf
│   ├── vpc.tf
│   ├── security.tf
│   ├── ec2.tf
│   ├── rds.tf
│   └── outputs.tf
│
├── infra/
│   ├── mysql/               ← DB init SQL + grants
│   ├── kafka/               ← create_topics.sh
│   ├── prometheus/
│   ├── grafana/
│   └── redis/
│
├── docker-compose.yml       ← local development
├── docker-compose.dev.yml   ← hot reload
├── docker-compose.test.yml  ← local AWS structure test
├── docker-compose.aws.yml   ← AWS EC2 deployment
├── deploy.sh                ← EC2 setup script
└── README.md
```

---

## API Reference

### User Service
```
POST /api/v1/users/register         → register new user
POST /api/v1/users/login            → login, returns JWT tokens
POST /api/v1/users/logout           → blacklist token
POST /api/v1/users/refresh          → refresh access token
GET  /api/v1/users/me               → get profile
POST /api/v1/users/admin/create-user→ admin creates delivery person
```

### Chef Service
```
POST  /api/v1/chefs/                    → create chef profile
GET   /api/v1/chefs/available/{city}    → browse available chefs
GET   /api/v1/chefs/user/{user_id}      → get chef by user id
PATCH /api/v1/chefs/{id}/status         → update availability
```

### Order Service
```
POST  /api/v1/orders/                   → place order
GET   /api/v1/orders/user/{user_id}     → customer order history
GET   /api/v1/orders/chef/{chef_id}     → chef active orders
PATCH /api/v1/orders/{id}/status        → chef updates status
POST  /api/v1/orders/{id}/cancel        → cancel order
```

### Delivery Service
```
GET   /api/v1/deliveries/available/{city}    → available deliveries
POST  /api/v1/deliveries/{id}/accept         → accept delivery
PATCH /api/v1/deliveries/{id}/status         → update status
GET   /api/v1/deliveries/person/{person_id}  → my deliveries
```

---

## Key Engineering Decisions

### 1. Why Microservices Over Monolith
Each service has independent deployment, scaling, and failure isolation. Chef assignment logic can scale independently from user authentication.

**Tradeoff accepted:** Higher operational complexity, network latency between services.

### 2. Why Kafka Over Direct HTTP Between Services
```
HTTP between services:
→ Tight coupling
→ If chef_service down → order placement fails
→ Synchronous = slow

Kafka:
→ order.created published → order_service returns 201 immediately
→ chef_service processes async
→ If chef_service restarts → replays unprocessed messages
→ At-least-once delivery guarantee
```

### 3. Why Per-Service Databases
Database-per-service pattern — no shared database = no tight coupling at data layer. Services cannot directly read each other's tables.

### 4. Why Redis For JWT Blacklist
JWT is stateless by design. Redis with TTL matching token expiry gives O(1) blacklist lookup with automatic expiry.

### 5. Why Nginx auth_request
Centralizes authentication without duplicating code in every service.

### 6. Why Terraform for AWS Infrastructure
Infrastructure as code — entire AWS setup reproducible with one command. Version controlled, documented, destroyable cleanly.

### 7. Why pool_pre_ping=False with aiomysql
Known incompatibility between SQLAlchemy 2.0.x pool_pre_ping and aiomysql non-root users. aiomysql manages connection health internally — disabling SQLAlchemy ping is the correct approach.

---

## Problems Encountered and Solved

### 1. bcrypt Version Conflict
**Problem:** `bcrypt==5.x` incompatible with `passlib==1.7.4`
**Fix:** Pin `bcrypt==4.0.1`

### 2. Kafka Healthcheck Failure in Docker
**Problem:** `ruok` command disabled in Zookeeper 3.8+
**Fix:** Use `cub zk-ready` instead of `echo ruok | nc`

### 3. Windows Port Conflicts
**Problem:** Windows reserves ports blocking Kafka and Prometheus
**Fix:** Move Prometheus to 9200, remove Kafka external port

### 4. Nginx DNS Difference — Docker vs Kubernetes
**Problem:** `resolver 127.0.0.11` (Docker DNS) doesn't exist in Kubernetes
**Fix:** Separate nginx configs per deployment — `10.96.0.10` for K8s, `127.0.0.11` for Docker
**Lesson:** Docker Compose DNS ≠ Kubernetes DNS

### 5. Kafka Service Name Conflict in Kubernetes
**Problem:** Kubernetes auto-injects `KAFKA_PORT` env var for Service named "kafka"
**Fix:** Rename Service to `kafka-broker`

### 6. MySQL admin User Access Denied on Non-Root
**Problem:** `MYSQL_USER=admin` created but not granted access to init databases
**Fix:** Added `init_grants.sql` — explicit GRANT ALL on each database to admin user
**Lesson:** MySQL auto-created users need explicit grants on non-default databases

### 7. pool_pre_ping Bug with aiomysql Non-Root User
**Problem:** SQLAlchemy `pool_pre_ping=True` calls `connection.ping()` without required argument when using aiomysql with non-root user
**Fix:** Set `pool_pre_ping=False` in all service `database.py` files
**Lesson:** Test with same user type (admin not root) locally before AWS deployment

### 8. Windows Port 3307 Forbidden
**Problem:** Docker couldn't bind port 3307 on Windows — reserved by Hyper-V
**Fix:** Removed port mapping from mysql_test — Docker internal networking doesn't need it
**Lesson:** Internal Docker services don't need host port mappings

### 9. Nginx Service URLs (Kubernetes → Docker Compose)
**Problem:** Nginx config used Kubernetes FQDN format for service URLs
**Fix:** Updated to Docker Compose service name format for aws branch
**Lesson:** Always validate nginx upstream URLs match your DNS environment

---

## Roadmap

```
✓ Phase 1-6  → 6 Microservices
✓ Phase 7    → Nginx + Security
✓ Phase 8    → Docker Compose (local)
✓ Phase 9    → Observability (Prometheus + Grafana)
✓ Phase 10   → Kubernetes Local
✓ Phase 11   → CI/CD (GitHub Actions)
✓ Phase 12   → AWS Deployment (EC2 + RDS + Terraform)
```
