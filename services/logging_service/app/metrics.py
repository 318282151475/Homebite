from prometheus_client import Counter

events_logged_total = Counter(
    name="events_logged_total",
    documentation="Total events logged to DB",
    labelnames=["event_type"],
)

logging_failures_total = Counter(
    name="logging_failures_total",
    documentation="Total logging failures",
)