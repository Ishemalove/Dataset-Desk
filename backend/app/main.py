import json
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.routes import analytics, auth, episodes, requests

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("dataset_desk")


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(title="Dataset Request Desk", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def structured_logging(request: Request, call_next):
    start = time.perf_counter()
    user_id = None
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            user_id = payload.get("sub")
        except JWTError:
            user_id = None

    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    log_entry = {
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": duration_ms,
        "user_id": user_id,
    }
    logger.info(json.dumps(log_entry))
    return response


@app.get("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"
    return {"status": "ok" if db_status == "ok" else "degraded", "database": db_status}


app.include_router(auth.router, prefix="/api")
app.include_router(requests.router, prefix="/api")
app.include_router(episodes.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
