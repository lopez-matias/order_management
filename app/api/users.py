from fastapi import APIRouter
from sqlalchemy import select

from app.api.dependencies import Database
from app.models import User
from app.schemas.orders import UserRead


router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
def list_users(db: Database) -> list[User]:
    return list(
        db.scalars(select(User).where(User.active.is_(True)).order_by(User.full_name)).all()
    )

