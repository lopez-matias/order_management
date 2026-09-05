from fastapi import APIRouter

from app.api.dependencies import Database
from app.schemas.dashboard import DashboardRead
from app.services.dashboard_service import get_dashboard


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardRead)
def dashboard(db: Database) -> DashboardRead:
    return get_dashboard(db)

