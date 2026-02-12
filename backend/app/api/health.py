import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.schemas.health import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])

START_TIME = time.time()


# -------------------------
# 🟢 Liveness Probe
# -------------------------
@router.get("/live", response_model=HealthResponse)
def liveness():
    """
    Liveness probe endpoint.
    Returns basic status and uptime.
    """
    return HealthResponse(
        status="healthy",
        details={"uptime_seconds": int(time.time() - START_TIME)}
    )


# -------------------------
# 🟡 Readiness Probe
# -------------------------
@router.get("/ready", response_model=HealthResponse)
def readiness(db: Session = Depends(get_db)):
    """
    Readiness probe endpoint.
    Checks if the database is reachable.
    """
    try:
        db.execute(text("SELECT 1"))
        return HealthResponse(
            status="healthy",
            details={"database": "connected"}
        )
    except Exception:
        return HealthResponse(
            status="unhealthy",
            details={"database": "not reachable"}
        )


# -------------------------
# 🔵 Global Health Summary
# -------------------------
@router.get("/", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    """
    Combined health endpoint.
    Checks database connectivity and reports uptime.
    """
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
        overall_status = "healthy"
    except Exception:
        db_status = "not reachable"
        overall_status = "unhealthy"

    return HealthResponse(
        status=overall_status,
        details={
            "database": db_status,
            "uptime_seconds": int(time.time() - START_TIME)
        }
    )