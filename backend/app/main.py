from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import time

from backend.app.api.routes import admin, auth, health, model_monitoring, properties, rankings, user_data, valuation, waitlist
from backend.app.core.config import get_settings
from backend.app.db.base import Base
from backend.app.db.session import engine

settings = get_settings()
app = FastAPI(title=settings.app_name)
_rate_window: dict[str, tuple[int, int]] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.allowed_origins.split(",")],
    allow_origin_regex=settings.allowed_origin_regex or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.middleware("http")
async def rate_limit_and_timing(request: Request, call_next):
    # Lightweight in-memory limiter for abuse protection in single-instance deploys.
    ip = request.client.host if request.client else "unknown"
    now_epoch = int(time.time())
    minute_bucket = now_epoch // 60
    count, bucket = _rate_window.get(ip, (0, minute_bucket))
    if bucket != minute_bucket:
        count = 0
        bucket = minute_bucket
    count += 1
    _rate_window[ip] = (count, bucket)

    if count > settings.rate_limit_per_minute:
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

    start = time.perf_counter()
    response = await call_next(request)
    latency_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time-Ms"] = f"{latency_ms:.2f}"
    return response


app.include_router(health.router)
app.include_router(properties.router)
app.include_router(valuation.router)
app.include_router(rankings.router)
app.include_router(waitlist.router)
app.include_router(auth.router)
app.include_router(user_data.router)
app.include_router(admin.router)
app.include_router(model_monitoring.router)
