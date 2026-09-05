from fastapi import APIRouter

from app.api import customers, dashboard, orders, products, users


api_router = APIRouter(prefix="/api")
api_router.include_router(dashboard.router)
api_router.include_router(customers.router)
api_router.include_router(products.router)
api_router.include_router(orders.router)
api_router.include_router(users.router)
