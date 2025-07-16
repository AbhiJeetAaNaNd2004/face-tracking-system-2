from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel

from utils.security import (
    verify_token, 
    require_admin, 
    get_db_manager, 
    create_access_token, 
    authenticate_user, 
    check_rate_limit,
    hash_password
)
from utils.logging import get_logger, log_authentication

logger = get_logger(__name__)

# FastAPI router
router = APIRouter(prefix="/auth", tags=["Authentication"])


# Pydantic Schemas
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str


# Additional Pydantic Schemas
class UserStatusRequest(BaseModel):
    new_status: str

class CreateUserRequest(BaseModel):
    username: str
    password: str
    role_id: int


# API Endpoints

@router.post("/login/", response_model=TokenResponse)
def login(login_request: LoginRequest, request: Request, db=Depends(get_db_manager)):
    """
    Authenticate user and return JWT access token.
    Includes rate limiting to prevent brute force attacks.
    """
    client_ip = request.client.host
    
    # Check rate limiting
    if not check_rate_limit(client_ip):
        log_authentication(logger, login_request.username, False, client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )
    
    # Authenticate user
    user_data = authenticate_user(login_request.username, login_request.password, db)
    
    if not user_data:
        log_authentication(logger, login_request.username, False, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create access token
    access_token = create_access_token({
        "sub": user_data["username"],
        "role": user_data["role"],
        "status": user_data["status"],
        "user_id": user_data["user_id"]
    })
    
    log_authentication(logger, login_request.username, True, client_ip)
    return TokenResponse(access_token=access_token)


@router.get("/secure/", response_model=MessageResponse)
def protected_endpoint(current_user: dict = Depends(verify_token)):
    username = current_user.get("sub")
    return MessageResponse(message=f"Hello {username}, you accessed a protected endpoint")


@router.get("/role-protected/", response_model=MessageResponse)
def admin_only_endpoint(current_user: dict = Depends(require_admin)):
    """Admin-only endpoint for testing role-based access control."""
    return MessageResponse(message=f"Admin endpoint accessed by {current_user.get('sub')}")

@router.patch("/users/{user_id}/status")
def update_user_status(
    user_id: int, 
    status_request: UserStatusRequest, 
    admin_user=Depends(require_admin), 
    db=Depends(get_db_manager)
):
    """Update user status (admin only)."""
    try:
        if status_request.new_status not in ["active", "inactive", "suspended"]:
            raise HTTPException(status_code=400, detail="Invalid status value")
        
        success = db.update_user_status(user_id, status_request.new_status)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"User {user_id} status updated to {status_request.new_status} by {admin_user.get('sub')}")
        return {"message": "User status updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/users/")
def create_user(
    user_request: CreateUserRequest, 
    admin_user=Depends(require_admin), 
    db=Depends(get_db_manager)
):
    """Create new user (admin only)."""
    try:
        # Hash password before storing
        hashed_password = hash_password(user_request.password)
        
        success = db.create_user(
            username=user_request.username,
            password_hash=hashed_password,
            role_id=user_request.role_id
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="User creation failed")
        
        logger.info(f"User {user_request.username} created by {admin_user.get('sub')}")
        return {"message": "User created successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
