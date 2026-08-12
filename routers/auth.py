from jose import jwt,JWTError
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException
from schemas import signup, login, ForgotPasswordRequest, ResetPasswordRequest
from databases import collection5
from utils import hash_password, verify_password, create_access_token

router = APIRouter()

RESET_SECRET_KEY = "YOUR_SUPER_SECRET_RESET_KEY"  # Store in environment variables
ALGORITHM = "HS256"

def create_reset_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    payload = {"sub": email, "exp": expire, "scope": "password_reset"}
    return jwt.encode(payload, RESET_SECRET_KEY, algorithm=ALGORITHM)

@router.post("/register")
def register_user(user_data: signup):
    existing_user = collection5.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    user_data.password = hash_password(user_data.password)
    current_user = collection5.insert_one({
        "email": user_data.email, 
        "password": user_data.password, 
        "username": user_data.username
    })
    
    data = {
        "email": user_data.email,
        "username": user_data.username,
        "user_id": str(current_user.inserted_id)
    }
    token = create_access_token(data)
    return {"message": "User registered successfully", "token": token}

@router.post("/login")
def login_user(user_data: login):
    user = collection5.find_one({"email": user_data.email})
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
        
    data = {
        "email": user["email"],
        "username": user["username"],
        "user_id": str(user["_id"])
    }
    token = create_access_token(data)
    return {"message": "User logged in successfully", "token": token}

@router.post("/forgot-password")
def forgot_password(user_data: ForgotPasswordRequest):
    user = collection5.find_one({"email": user_data.email})
    if not user:
        # Don't reveal account existence for security
        return {"message": "If an account exists with this email, a reset link has been issued."}

    reset_token = create_reset_token(user_data.email)
    
    # In production, dispatch reset_token via email (SMTP / SendGrid)
    return {
        "message": "Reset token generated successfully",
        "reset_token": reset_token
    }

@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest):
    try:
        payload = jwt.decode(data.token, RESET_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("scope") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid token type")
        email = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Reset token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    user = collection5.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_hashed_password = hash_password(data.new_password)
    collection5.update_one({"email": email}, {"$set": {"password": new_hashed_password}})

    return {"message": "Password updated successfully. You can now log in."}