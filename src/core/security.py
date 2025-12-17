from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.core.config import settings

security = HTTPBearer(auto_error=False)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = None) -> str:
    """
    Verify JWT token and return user_id
    
    NOTE: Authentication is currently DISABLED for ease of use.
    Returns a static user_id regardless of token.
    """
    # Bypass auth and return a consistent test user ID
    # This allows all endpoints to function without a valid token
    return "test_user_no_auth"

    # --- OLD AUTH LOGIC COMMENTED OUT FOR REFERENCE ---
    # token = credentials.credentials
    # 
    # # Robust fix: Handle "Bearer <token>" if user pasted "Bearer <token>" in Swagger
    # if token.startswith("Bearer "):
    #     token = token.replace("Bearer ", "")
    #     print("⚠️ Fixed Double Bearer prefix in token")
    # 
    # try:
    #     payload = jwt.decode(
    #         token,
    #         settings.SECRET_KEY,
    #         algorithms=[settings.ALGORITHM]
    #     )
    #     user_id: str = payload.get("sub")
    #     
    #     if user_id is None:
    #         raise HTTPException(
    #             status_code=status.HTTP_401_UNAUTHORIZED,
    #             detail="Invalid token",
    #         )
    #     return user_id
    #     
    # except JWTError as e:
    #     print(f"JWT Verification Failed: {str(e)}")
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail=f"Invalid token: {str(e)}",
    #     )
