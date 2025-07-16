from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from db.db_manager import DatabaseManager
from db.db_models import User
import bcrypt
import jwt
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Configurable secret for JWT
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBearer()

# FastAPI router
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Database dependency
db_manager_instance = None

def get_db_manager():
    global db_manager_instance
    if db_manager_instance is None:
        db_manager_instance = DatabaseManager()
    return db_manager_instance


# Pydantic Schemas
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str


# Helper Functions

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("status") != "active":
            raise HTTPException(status_code=403, detail="Account inactive or suspended")
        return payload  # includes username, role, status
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# API Endpoints

@router.post("/login/", response_model=TokenResponse)
def login(login_request: LoginRequest, db: DatabaseManager = Depends(get_db_manager)):
    user = db.get_user_by_username(login_request.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    if user.status != "active":
        raise HTTPException(status_code=403, detail="Account inactive or suspended")

    if not bcrypt.checkpw(login_request.password.encode(), user.password_hash.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    access_token = create_access_token({
        "sub": user.username,
        "role": user.role.role_name if user.role else "user",
        "status": user.status
    })

    return TokenResponse(access_token=access_token)


@router.get("/secure/", response_model=MessageResponse)
def protected_endpoint(current_user: dict = Depends(verify_token)):
    username = current_user.get("sub")
    return MessageResponse(message=f"Hello {username}, you accessed a protected endpoint")


@router.get("/role-protected/", response_model=MessageResponse)
def admin_only_endpoint(current_user: dict = Depends(verify_token)):
    role = current_user.get("role")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return MessageResponse(message=f"Admin endpoint accessed by {current_user.get('sub')}")
