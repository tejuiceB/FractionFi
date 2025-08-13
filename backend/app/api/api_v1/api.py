from fastapi import APIRouter
from app.api.api_v1.endpoints import auth, bonds, orders, users, portfolio, admin, websocket

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(bonds.router, prefix="/bonds", tags=["bonds"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
