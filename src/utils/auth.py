from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.configs.settings import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
)

class JWTAuth:
    """JWT Authentication handler class"""
    
    # Class-level HTTP bearer security scheme
    security = HTTPBearer()
    
    @classmethod
    def create_access_token(cls, data: Dict[str, Any] = None, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token with optional payload and expiration time
        
        Args:
            data: Dictionary of data to encode in the token
            expires_delta: Optional override for token expiration time
            
        Returns:
            Encoded JWT token as string
        """
        to_encode = data or {}
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    
    @classmethod
    async def verify_token(cls, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """
        Verify JWT token from Authorization header
        
        Args:
            credentials: Bearer token credentials from HTTP Authorization header
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                credentials.credentials, 
                JWT_SECRET_KEY, 
                algorithms=[JWT_ALGORITHM]
            )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    @classmethod
    def get_token_verify_dependency(cls):
        """
        Returns a dependency function that verifies the JWT token
        
        Usage:
            @app.get("/protected")
            async def protected_route(token_data: dict = Depends(JWTAuth.get_token_verify_dependency())):
                return {"message": "This is protected", "token_data": token_data}
        """
        return cls.verify_token
    
    @classmethod
    async def generate_token(cls) -> Dict[str, str]:
        """
        Generate a simple JWT token with default settings
        
        Returns:
            Dictionary with access token and token type
        """
        token = cls.create_access_token()
        return {"access_token": token, "token_type": "bearer"}
