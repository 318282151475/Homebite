from prometheus_client import Counter

users_registered_total = Counter(
    name="users_registered_total",
    documentation="Total number of users registered",
    labelnames=["role"],
)

login_attempts_total = Counter(
    name="login_attempts_total",
    documentation="Total login attempts",
    labelnames=["status"],  # success or failed
)

token_blacklisted_total = Counter(
    name="token_blacklisted_total",
    documentation="Total tokens blacklisted (logouts)",
)