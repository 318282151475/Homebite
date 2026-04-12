from prometheus_client import Counter, Gauge, Histogram

# Counter — only goes up, never down
# Use for: requests, errors, events published, orders placed
orders_placed_total = Counter(
    name="orders_placed_total",
    documentation="Total number of orders placed",
)

orders_failed_total = Counter(
    name="orders_failed_total",
    documentation="Total number of orders that failed (no chef available)",
)

orders_cancelled_total = Counter(
    name="orders_cancelled_total",
    documentation="Total number of orders cancelled by user",
)

kafka_events_published_total = Counter(
    name="kafka_events_published_total",
    documentation="Total Kafka events published",
    labelnames=["topic"],  # track per topic
)

# Gauge — goes up and down
# Use for: active connections, current queue size, items in progress
orders_in_progress = Gauge(
    name="orders_in_progress",
    documentation="Number of orders currently being processed",
)