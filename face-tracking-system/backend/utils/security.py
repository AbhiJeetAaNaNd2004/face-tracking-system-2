"""
Centralized security utilities for authentication and authorization.
This module provides reusable functions for JWT token handling, password management,
and access control to eliminate code duplication across routers.
"""

import jwt
import bcrypt
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from collections import defaultdict

from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings
from db.db_manager import DatabaseManager

# Security setup
security = HTTPBearer()

# Rate limiting storage
login_attempts = defaultdict(list)
MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_MINUTES = 15

# Database dependency
db_manager_instance = None

def get_db_manager():
    """Get database manager instance (singleton pattern)"""
    global db_manager_instance
    if db_manager_instance is None:
        db_manager_instance = DatabaseManager()
    return db_manager_instance

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with the provided data.
    
    Args:
        data: Dictionary containing token payload
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """
    Verify JWT token and return payload.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        Token payload dictionary
        
    Raises:
        HTTPException: If token is invalid, expired, or user is inactive
    """
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Check if token is expired
        current_time = datetime.utcnow()
        exp_time = datetime.utcfromtimestamp(payload.get("exp", 0))
        if current_time >= exp_time:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check if user is active
        if payload.get("status") != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account inactive or suspended"
            )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )

def require_admin(token_data: Dict = Depends(verify_token)) -> Dict:
    """
    Require admin role for endpoint access.
    
    Args:
        token_data: Token payload from verify_token
        
    Returns:
        Token payload if user is admin
        
    Raises:
        HTTPException: If user is not admin
    """
    if token_data.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return token_data

def require_roles(allowed_roles: List[str]):
    """
    Create a dependency that requires specific roles.
    
    Args:
        allowed_roles: List of allowed role names
        
    Returns:
        Dependency function for FastAPI
    """
    def role_checker(token_data: Dict = Depends(verify_token)) -> Dict:
        user_role = token_data.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {', '.join(allowed_roles)}"
            )
        return token_data
    return role_checker

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password
        hashed_password: Stored password hash
        
    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def check_rate_limit(client_ip: str) -> bool:
    """
    Check if client IP is within rate limit for login attempts.
    
    Args:
        client_ip: Client IP address
        
    Returns:
        True if within rate limit, False if exceeded
    """
    current_time = time.time()
    cutoff_time = current_time - (LOGIN_WINDOW_MINUTES * 60)
    
    # Clean old attempts
    login_attempts[client_ip] = [
        attempt for attempt in login_attempts[client_ip] 
        if attempt > cutoff_time
    ]
    
    # Check if limit exceeded
    if len(login_attempts[client_ip]) >= MAX_LOGIN_ATTEMPTS:
        return False
    
    # Add current attempt
    login_attempts[client_ip].append(current_time)
    return True

def authenticate_user(username: str, password: str, db: DatabaseManager) -> Optional[Dict]:
    """
    Authenticate user with username and password.
    
    Args:
        username: Username
        password: Plain text password
        db: Database manager instance
        
    Returns:
        User data dictionary if authenticated, None otherwise
    """
    user = db.get_user_by_username(username)
    if not user:
        return None
    
    if user.status != "active":
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    return {
        "username": user.username,
        "role": user.role.role_name if user.role else "user",
        "status": user.status,
        "user_id": user.id
    }