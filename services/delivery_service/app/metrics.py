from prometheus_client import Counter, Histogram

deliveries_created_total = Counter(
    name="deliveries_created_total",
    documentation="Total deliveries created",
)

deliveries_completed_total = Counter(
    name="deliveries_completed_total",
    documentation="Total deliveries completed",
)

deliveries_failed_total = Counter(
    name="deliveries_failed_total",
    documentation="Total deliveries failed",
)

# Histogram — tracks distribution of values
# Use for: delivery time, response time, payload size
delivery_duration_minutes = Histogram(
    name="delivery_duration_minutes",
    documentation="Time taken to complete delivery in minutes",
    # buckets define the ranges you want to track
    buckets=[15, 30, 45, 60, 90, 120],
)