"""
Authentication API Routes
JWT-based authentication for dashboard access
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
import logging

from app.db.postgres import get_db
from app.core.security import verify_password, create_access_token, decode_access_token

logger = logging.getLogger(__name__)

router = APIRouter()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# Request/Response models
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserLogin(BaseModel):
    username: str
    password: str


class User(BaseModel):
    username: str
    is_active: bool = True


# Default admin credentials (in production, use environment variables)
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"  # In production, hash this and store in DB


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        token: JWT token from Authorization header
    
    Returns:
        User object
    """
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return User(username=username)


@router.post("/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login endpoint for dashboard access.
    Default credentials: admin / admin123
    """
    # Simple authentication (in production, verify against database)
    if form_data.username == DEFAULT_ADMIN_USERNAME and form_data.password == DEFAULT_ADMIN_PASSWORD:
        access_token = create_access_token(data={"sub": form_data.username})
        logger.info(f"User {form_data.username} logged in successfully")
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information.
    """
    return current_user


@router.post("/auth/verify")
async def verify_token(token_data: dict):
    """
    Verify if a token is valid.
    """
    token = token_data.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Token is required")
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"valid": True, "username": payload.get("sub")}
