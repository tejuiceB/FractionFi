from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.db.database import get_db
from app.models.models import User
from app.core.auth import get_current_active_user

router = APIRouter()

class UserCreate(BaseModel):
    wallet_address: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    wallet_address: str
    email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    kyc_verified: bool
    created_at: str
    
    class Config:
        from_attributes = True

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with wallet address"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.wallet_address == user_data.wallet_address).first()
    if existing_user:
        return UserResponse(
            id=existing_user.id,
            wallet_address=existing_user.wallet_address,
            email=existing_user.email,
            first_name=existing_user.first_name,
            last_name=existing_user.last_name,
            kyc_verified=existing_user.kyc_verified,
            created_at=existing_user.created_at.isoformat()
        )
    
    # Create new user
    new_user = User(
        wallet_address=user_data.wallet_address,
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role="investor",  # Default role
        kyc_verified=False  # Require KYC verification
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse(
        id=new_user.id,
        wallet_address=new_user.wallet_address,
        email=new_user.email,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        kyc_verified=new_user.kyc_verified,
        created_at=new_user.created_at.isoformat()
    )

@router.get("/me")
async def get_current_user(current_user: User = Depends(get_current_active_user)):
    """Get current authenticated user"""
    return UserResponse(
        id=current_user.id,
        wallet_address=current_user.wallet_address,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        kyc_verified=current_user.kyc_verified,
        created_at=current_user.created_at.isoformat()
    )

@router.get("/{user_id}")
async def get_user(user_id: str):
    return {"message": f"User {user_id} endpoint"}
