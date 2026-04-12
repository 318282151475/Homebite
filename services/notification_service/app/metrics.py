from prometheus_client import Counter

notifications_sent_total = Counter(
    name="notifications_sent_total",
    documentation="Total notifications sent",
    labelnames=["type"],  # email, sms
)

notifications_failed_total = Counter(
    name="notifications_failed_total",
    documentation="Total notifications failed",
    labelnames=["type"],
)