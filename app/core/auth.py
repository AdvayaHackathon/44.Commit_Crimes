import os
import logging
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.core.database import User, get_db

# Set up logging
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-jwt")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

def verify_password(plain_password, hashed_password):
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Generate a password hash"""
    return pwd_context.hash(password)

def create_user(db: Session, username: str, email: str, password: str, full_name: str, role: str):
    """Create a new user"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            if existing_user.username == username:
                return {"error": "Username already registered"}
            else:
                return {"error": "Email already registered"}
        
        # Create new user
        hashed_password = get_password_hash(password)
        db_user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            full_name=full_name,
            role=role
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {str(e)}")
        return {"error": str(e)}

def authenticate_user(db: Session, username: str, password: str):
    """Authenticate a user"""
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        return False
    
    if not verify_password(password, user.password_hash):
        return False
    
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def get_current_user(token: str, db: Session):
    """Get the current user from a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if user_id is None:
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except jwt.PyJWTError:
        return None
