from prometheus_client import Counter, Gauge

chefs_assigned_total = Counter(
    name="chefs_assigned_total",
    documentation="Total number of chef assignments",
)

chef_assignment_failed_total = Counter(
    name="chef_assignment_failed_total",
    documentation="Total number of failed chef assignments",
)

# Gauge — current snapshot
chefs_available = Gauge(
    name="chefs_available_total",
    documentation="Number of chefs currently available",
    labelnames=["city"],
)

kafka_events_consumed_total = Counter(
    name="kafka_events_consumed_total",
    documentation="Total Kafka events consumed",
    labelnames=["topic", "event_type"],
)