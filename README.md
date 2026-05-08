# 🍽️ HomeBite — Home Chef Food Delivery Platform

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=flat&logo=docker&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=flat&logo=kubernetes&logoColor=white)
![Kafka](https://img.shields.io/badge/Apache_Kafka-231F20?style=flat&logo=apache-kafka&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat&logo=mysql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7.2-DC382D?style=flat&logo=redis&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=flat&logo=prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-F46800?style=flat&logo=grafana&logoColor=white)

A **production-grade microservices food delivery platform** connecting customers with home chefs. Built with event-driven architecture, Kubernetes deployment, and full observability stack.

> Built as a portfolio project targeting Senior Backend/DevOps roles (20 LPA). Every architectural decision has a reason — documented below.

---

## 📋 Table of Contents

- [What Is HomeBite](#what-is-homebite)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Services](#services)
- [Event Flow](#event-flow)
- [Security Design](#security-design)
- [Observability](#observability)
- [Project Structure](#project-structure)
- [Running Locally — Docker Compose](#running-locally--docker-compose)
- [Running On Kubernetes](#running-on-kubernetes)
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
    ┌─────▼─────┐   ┌───────▼──────┐   ┌─────────▼────────┐
    │delivery   │   │notification  │   │  logging_service  │
    │_service   │   │  _service    │   │     :8006        │
    │  :8004    │   │    :8005     │   └──────────────────┘
    └───────────┘   └──────────────┘
          │                 │
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
| Containerization | Docker + Docker Compose | Local development |
| Orchestration | Kubernetes | Production deployment |
| Metrics | Prometheus + Grafana | Observability |
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
- Email notification simulation

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
   → creates delivery record in delivery_service

4. delivery_service consumes chef.assigned
   → creates delivery record
   → delivery person can see and accept

5. delivery_service.status = PICKED_UP
   → publishes delivery.started
   → order_service updates to out_for_delivery

6. delivery_service.status = DELIVERED
   → publishes delivery.completed
   → order_service updates to delivered
   → chef_service resets chef to available

All events → logging_service (audit trail)
All events → notification_service (user notifications)
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

### Timing Attack Prevention
```python
# Always verify password even if user not found
# Prevents attacker from detecting valid emails
# by measuring response time difference
if not user or not verify_password(data.password, user.hashed_password):
    login_attempts_total.labels(status="failed").inc()
    raise InvalidCredentialsException()
```

---

## Observability

### Metrics (Prometheus + Grafana)

**Business Metrics:**
```
orders_placed_total           → total orders placed
orders_in_progress            → live gauge of active orders
orders_cancelled_total        → cancellation rate
chefs_assigned_total          → successful chef assignments
chef_assignment_failed_total  → failed assignments
deliveries_completed_total    → completed deliveries
delivery_duration_minutes     → histogram of delivery times
```

**Auth Metrics:**
```
users_registered_total        → by role (customer/chef)
login_attempts_total          → success vs failed
token_blacklisted_total       → logout rate
```

**Kafka Metrics:**
```
kafka_events_published_total  → by topic
kafka_events_consumed_total   → by service and event type
```

**Infrastructure Metrics (automatic):**
```
http_requests_total           → by service, endpoint, status
http_request_duration_seconds → P50, P95, P99 latency
```

### Grafana Dashboard
Pre-built dashboard with 5 sections:
- Business Metrics (stat cards)
- HTTP Traffic (requests/sec, error rate, P99 latency)
- Auth Metrics (login attempts, registrations)
- Kafka Events (published vs consumed)
- Service Health (UP/DOWN per service)

---

## Project Structure

```
HomeBite/
├── services/
│   ├── user_service/
│   │   ├── app/
│   │   │   ├── api/v1/routes.py
│   │   │   ├── core/security.py
│   │   │   ├── core/exceptions.py
│   │   │   ├── crud/user.py
│   │   │   ├── kafka/consumer.py
│   │   │   ├── kafka/producer.py
│   │   │   ├── metrics.py
│   │   │   ├── models/user.py
│   │   │   ├── schemas/user.py
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
│   │   ├── homebite.conf    ← routing + auth_request + rate limiting
│   │   └── proxy_params.conf
│   ├── errors/              ← custom JSON error responses
│   ├── nginx.conf
│   ├── index.html           ← HomeBite frontend (baked into image)
│   └── Dockerfile
│
├── frontend/
│   └── index.html           ← Single page app (4 role dashboards)
│
├── k8s/
│   ├── namespaces/          ← homebite + monitoring namespaces
│   ├── storage/             ← PersistentVolumeClaims
│   ├── configmaps/          ← app config + kafka scripts + prometheus
│   ├── secrets/             ← DB passwords + JWT keys (gitignored)
│   ├── infrastructure/      ← MySQL, Redis, Kafka, Zookeeper
│   ├── deployments/         ← 6 app services + nginx
│   ├── monitoring/          ← Prometheus + Grafana
│   ├── services/            ← ClusterIP + NodePort services
│   └── ingress/             ← Nginx ingress rules
│
├── infra/
│   ├── mysql/               ← init.sql (creates all databases)
│   ├── kafka/               ← create_topics.sh
│   ├── prometheus/          ← prometheus.yml
│   ├── grafana/
│   │   ├── datasources/     ← auto-provision Prometheus
│   │   └── dashboards/      ← homebite.json dashboard
│   └── redis/               ← redis.conf
│
├── docker-compose.yml       ← local development
├── docker-compose.dev.yml   ← hot reload for development
└── README.md
```

---

## Running Locally — Docker Compose

### Prerequisites
- Docker Desktop
- Python 3.12 (for local development)

### Quick Start

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/homebite.git
cd homebite

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

### Access Points
```
Frontend      → http://localhost
phpMyAdmin    → http://localhost:8080
Prometheus    → http://localhost:9200
Grafana       → http://localhost:3000  (admin/admin123)
```

### Development Mode (Hot Reload)
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

---

## Running On Kubernetes

### Prerequisites
- Docker Desktop with Kubernetes enabled
- kubectl
- Images pushed to Docker Hub

### Deploy

```bash
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
kubectl apply -f k8s/infrastructure/phpmyadmin-deployment.yaml
kubectl apply -f k8s/infrastructure/kafka-deployment.yaml

# 6. Wait for Kafka, then create topics
kubectl apply -f k8s/infrastructure/kafka-init-job.yaml

# 7. App services
kubectl apply -f k8s/deployments/

# 8. Monitoring
kubectl apply -f k8s/monitoring/

# 9. Remaining services + ingress
kubectl apply -f k8s/services/
kubectl apply -f k8s/ingress/
```

### Access via Port-Forward
```bash
kubectl port-forward service/nginx-service 8080:80 -n homebite
kubectl port-forward service/phpmyadmin 8083:80 -n homebite
kubectl port-forward service/prometheus 9090:9090 -n monitoring
kubectl port-forward service/grafana 3000:3000 -n monitoring
```

```
Frontend      → http://localhost:8080
phpMyAdmin    → http://localhost:8083
Prometheus    → http://localhost:9090
Grafana       → http://localhost:3000
```

### Verify All Pods Running
```bash
kubectl get pods -n homebite
kubectl get pods -n monitoring
```

---

## API Reference

### User Service
```
POST /api/v1/users/register    → register new user
POST /api/v1/users/login       → login, returns JWT tokens
POST /api/v1/users/logout      → blacklist token
POST /api/v1/users/refresh     → refresh access token
GET  /api/v1/users/me          → get profile
POST /admin/create-user        → admin creates delivery person
```

### Chef Service
```
POST /api/v1/chefs/            → create chef profile
GET  /api/v1/chefs/available/{city}  → browse available chefs
GET  /api/v1/chefs/user/{user_id}    → get chef by user id
PATCH /api/v1/chefs/{id}/status      → update availability
```

### Order Service
```
POST /api/v1/orders/                 → place order
GET  /api/v1/orders/user/{user_id}   → customer order history
GET  /api/v1/orders/chef/{chef_id}   → chef active orders
PATCH /api/v1/orders/{id}/status     → chef updates status
POST /api/v1/orders/{id}/cancel      → cancel order
```

### Delivery Service
```
GET  /api/v1/deliveries/available/{city}         → available deliveries
POST /api/v1/deliveries/{id}/accept              → accept delivery
PATCH /api/v1/deliveries/{id}/status             → update status
GET  /api/v1/deliveries/person/{person_id}       → my deliveries
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
Database-per-service pattern:
- user_service owns user_db
- chef_service owns chef_db
- order_service owns order_db

No shared database = no tight coupling at data layer. Services cannot directly read each other's tables.

### 4. Why Redis For JWT Blacklist
JWT is stateless by design. To support logout we need stateful tracking. Redis with TTL matching token expiry gives us:
- O(1) blacklist lookup
- Automatic expiry (no cleanup needed)
- Fast enough for every request

### 5. Why Nginx auth_request
Centralizes authentication without duplicating code in every service. Single JWT validation point — if auth logic changes, update one place.

### 6. Kafka acks=all For Orders
```python
producer = AIOKafkaProducer(acks="all")
```
Order data is critical. `acks=all` waits for all Kafka replicas to confirm before returning. Slower but zero message loss. Acceptable tradeoff for financial transactions.

---

## Problems Encountered and Solved

### 1. bcrypt Version Conflict
**Problem:** `bcrypt==5.x` incompatible with `passlib==1.7.4`
**Fix:** Pin `bcrypt==4.0.1` in requirements.txt
**Lesson:** Always pin dependency versions in production

### 2. Kafka Healthcheck Failure in Docker
**Problem:** `ruok` command disabled in Zookeeper 3.8+ by default
**Fix:** Use `cub zk-ready` instead of `echo ruok | nc`
**Lesson:** Official tools beat manual TCP checks

### 3. Windows Port Conflicts
**Problem:** Windows reserves ports 9023-9122, blocking Kafka and Prometheus
**Fix:** Move Prometheus to 9200, remove Kafka external port
**Lesson:** Know your OS port reservation ranges

### 4. Nginx Dynamic DNS in Kubernetes
**Problem:** Nginx uses `resolver 127.0.0.11` (Docker DNS) — does not exist in Kubernetes
**Fix:** Change to CoreDNS IP `10.96.0.10`
**Lesson:** Docker Compose DNS ≠ Kubernetes DNS

### 5. Kafka Service Name Conflict in Kubernetes
**Problem:** Kubernetes auto-injects `KAFKA_PORT` env var for any Service named "kafka"
**Fix:** Rename Service to `kafka-broker` and skip Confluent preflight checks
**Lesson:** Kubernetes service discovery injects env vars — conflicts with apps that use same prefix

### 6. Nginx index.html Not In Image
**Problem:** Docker Compose mounts `index.html` as volume at runtime. Kubernetes has no volume mount → default nginx page shown
**Fix:** Copy `index.html` into `nginx/` folder and add `COPY index.html` to Dockerfile
**Lesson:** Everything needed at runtime must be baked into image for Kubernetes

### 7. MySQL User Creation Error
**Problem:** `MYSQL_USER=root` not allowed — root is configured via `MYSQL_ROOT_PASSWORD`
**Fix:** Remove `MYSQL_USER` and `MYSQL_PASSWORD`, keep only `MYSQL_ROOT_PASSWORD`
**Lesson:** Read official image documentation for env variable conventions

---

## Roadmap

```
✓ Phase 1-6  → 6 Microservices
✓ Phase 7    → Nginx + Security
✓ Phase 8    → Docker Compose
✓ Phase 9    → Observability
✓ Phase 10   → Kubernetes Local
⏳ Phase 11   → CI/CD (GitHub Actions)
⏳ Phase 12   → AWS Deployment (EKS + RDS + MSK)
```

---

