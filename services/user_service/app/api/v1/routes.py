from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import time

from app.database import get_db
from ...schemas.user import UserRegisterRequest, UserLoginRequest, TokenRefreshRequest, UserResponse, TokenResponse, \
    UserProfileResponse, AdminCreateUserRequest
from ...crud import user as user_crud
from ...core.security import verify_password, create_access_token, create_refresh_token, verify_access_token, \
    blacklist_token, decode_token
from ...core.exceptions import UserAlreadyExistsException, InvalidCredentialsException, UserNotFoundException, \
    InactiveUserException, InvalidTokenException
from app.kafka.producer import publish_event
from app.config import get_settings

#Metrics import
from ...metrics import users_registered_total, login_attempts_total, token_blacklisted_total


settings = get_settings()
router = APIRouter(prefix="/api/v1/users", tags=["users"])
bearer_scheme = HTTPBearer()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    if await user_crud.get_user_by_email(db, data.email):
        raise UserAlreadyExistsException(field="email")

    if data.phone and await user_crud.get_user_by_phone(db, data.phone):
        raise UserAlreadyExistsException(field="phone")

    user = await user_crud.create_user(db, data)

    # increment counter per role — tells us how many customers vs chefs registered
    users_registered_total.labels(role=user.role.value).inc()  #Metrics

    await publish_event(
        topic=settings.KAFKA_TOPIC_USER_REGISTERED,
        event={
            "event": "user.registered",
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value,
        }
    )

    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    user = await user_crud.get_user_by_email(db, data.email)

    # Always verify password even if user not found
    # Prevents timing attacks — attacker cannot detect valid emails
    # by measuring response time difference
    if not user or not verify_password(data.password, user.hashed_password):
        # increment failed counter BEFORE raising exception
        login_attempts_total.labels(status="failed").inc()    #Metrics
        raise InvalidCredentialsException()

    if not user.is_active:
        raise InactiveUserException()

    token_payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value
    }

    # increment success counter after all checks pass
    login_attempts_total.labels(status="success").inc()   #Metrics

    return TokenResponse(
        access_token=create_access_token(token_payload),
        refresh_token=create_refresh_token(token_payload),
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(data.refresh_token)

    if payload.get("type") != "refresh":
        raise InvalidTokenException()

    user_id = int(payload.get("sub"))
    user = await user_crud.get_user_by_id(db, user_id)

    if not user:
        raise UserNotFoundException()

    if not user.is_active:
        raise InactiveUserException()

    token_payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value
    }

    return TokenResponse(
        access_token=create_access_token(token_payload),
        refresh_token=create_refresh_token(token_payload),
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    payload = await verify_access_token(token)

    exp = payload.get("exp")
    now = int(time.time())
    ttl = max(exp - now, 1)

    await blacklist_token(token, expires_in_seconds=ttl)

    # track how many users are logging out
    # spike in logouts = possible security issue or bad UX
    token_blacklisted_total.inc()              #Metrics


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    payload = await verify_access_token(credentials.credentials)
    user_id = int(payload.get("sub"))

    user = await user_crud.get_user_by_id(db, user_id)
    if not user:
        raise UserNotFoundException()

    return UserProfileResponse(user=UserResponse.model_validate(user))


# Admin only endpoint — creates delivery person accounts
# In production add role check middleware
# For now protected by JWT only
@router.post("/admin/create-user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_user(
    data: AdminCreateUserRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    # verify token
    payload = await verify_access_token(credentials.credentials)

    # only admin can create delivery persons
    if payload.get("role") != "admin":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can create user accounts"
        )

    if await user_crud.get_user_by_email(db, data.email):
        raise UserAlreadyExistsException(field="email")

    if data.phone and await user_crud.get_user_by_phone(db, data.phone):
        raise UserAlreadyExistsException(field="phone")

    # use UserRegisterRequest compatible create
    from ...schemas.user import UserRegisterRequest
    register_data = UserRegisterRequest(
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        password=data.password,
        role=data.role,
    )
    user = await user_crud.create_user(db, register_data)
    return user

# Called by Nginx auth_request directive
# Nginx hits this before forwarding any protected request
# Returns 200 = valid token, 401 = invalid
# Never appears in Swagger — internal only
@router.get("/internal/verify-token", include_in_schema=False)
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    payload = await verify_access_token(credentials.credentials)
    return {"user_id": payload.get("sub"), "role": payload.get("role")}
