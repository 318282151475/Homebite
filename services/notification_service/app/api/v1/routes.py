from fastapi import APIRouter

# notification_service has no public API endpoints
# It is purely event-driven — only reacts to Kafka events
# The only HTTP endpoint exposed is /health for Kubernetes probes
router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])