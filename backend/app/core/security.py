# backend/app/core/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import settings

security_scheme = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

def get_current_agent(credentials: HTTPAuthorizationCredentials = Security(security_scheme)) -> dict:
    """Get current authenticated agent from JWT token."""
    token = credentials.credentials
    payload = verify_token(token)
    agent_id = payload.get("sub")
    if agent_id is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return {"agent_id": agent_id}

def verify_service_token(token: str) -> bool:
    """Verify service token for worker-to-backend communication."""
    return token == settings.SERVICE_TOKEN
