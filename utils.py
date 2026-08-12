import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext

load_dotenv()

Auth_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

expire_time = int(os.getenv("expire_time", "30"))
secret_key = os.getenv("secret_key", "default_fallback_secret")
algorithm = os.getenv("Algorithm", "HS256")

def create_access_token(data: dict, expire_timedelta: timedelta | None = None):
    copy_data = data.copy()
    if expire_timedelta:
        expire = datetime.now(timezone.utc) + expire_timedelta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=expire_time)

    copy_data.update({"exp": expire})
    return jwt.encode(copy_data, secret_key, algorithm=algorithm)

def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=401, 
            detail="Invalid credentials: Try Again", 
            headers={"WWW-Authenticate": "Bearer"}
        )

def get_current_user(token: str = Depends(Auth_scheme)):
    return verify_access_token(token)

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)