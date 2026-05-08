from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import asyncio
import logging
import time
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import get_settings
from app.database import engine, Base
from app.api.v1.routes import router
from app.kafka.consumer import start_consumer, stop_consumer, consume_events

settings = get_settings()
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME}...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await start_consumer()
    consumer_task = asyncio.create_task(consume_events())

    logger.info(f"{settings.APP_NAME} started. Consuming all Kafka topics.")
    yield

    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

    await stop_consumer()
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Prometheus metrics
# Exposes /metrics endpoint automatically
# Tracks: request count, response time, status codes — all by endpoint
Instrumentator().instrument(app).expose(app)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    process_time = time.time() - start
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2)) + "ms"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.APP_NAME}