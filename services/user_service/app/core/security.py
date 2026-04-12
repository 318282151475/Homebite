from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import redis.asyncio as aioredis
from app.config import get_settings
from app.core.exceptions import InvalidTokenException, TokenRevokedException

settings = get_settings()

# bcrypt = industry standard password hashing
# deprecated="auto" = auto upgrades old hashes
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(payload: dict) -> str:
    data = payload.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    data.update({"exp": expire, "type": "access"})
    return jwt.encode(data, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(payload: dict) -> str:
    data = payload.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    data.update({"exp": expire, "type": "refresh"})
    return jwt.encode(data, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise InvalidTokenException()


async def get_redis_client() -> aioredis.Redis:
    return aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )


async def blacklist_token(token: str, expires_in_seconds: int) -> None:
    redis = await get_redis_client()
    await redis.setex(
        name=f"blacklisted:{token}",
        time=expires_in_seconds,
        value="true"
    )
    await redis.aclose()


async def is_token_blacklisted(token: str) -> bool:
    redis = await get_redis_client()
    result = await redis.get(f"blacklisted:{token}")
    await redis.aclose()
    return result is not None


async def verify_access_token(token: str) -> dict:
    # Step 1: decode and validate signature + expiry
    payload = decode_token(token)

    # Step 2: ensure it's an access token not refresh token
    if payload.get("type") != "access":
        raise InvalidTokenException()

    # Step 3: check Redis blacklist (user logged out)
    if await is_token_blacklisted(token):
        raise TokenRevokedException()

    return payload