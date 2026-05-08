from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from ..models.user import User
from ..schemas.user import UserRegisterRequest
from ..core.security import hash_password


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_phone(db: AsyncSession, phone: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.phone == phone))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, data: UserRegisterRequest) -> User:
    user = User(
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        hashed_password=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    # flush → sends INSERT to DB without committing
    # lets us access user.id before transaction closes
    await db.flush()
    await db.refresh(user)
    return user


async def deactivate_user(db: AsyncSession, user_id: int) -> Optional[User]:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    user.is_active = False
    await db.flush()
    await db.refresh(user)
    return user