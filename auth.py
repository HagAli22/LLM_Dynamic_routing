"""Authentication and Authorization - JWT based"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session
import os

from database import get_db, User

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production-123456")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
http_bearer = HTTPBearer(auto_error=False)


# ==================== PASSWORD HASHING ====================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password using bcrypt directly
    
    Args:
        plain_password: The plain text password
        hashed_password: The bcrypt hashed password
        
    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        # Convert strings to bytes if needed
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        
        return bcrypt.checkpw(plain_password, hashed_password)
    except Exception as e:
        print(f"⚠️ Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    Hash password using bcrypt directly
    
    Args:
        password: The plain text password to hash
        
    Returns:
        str: The bcrypt hashed password
    """
    try:
        # Convert to bytes if needed
        if isinstance(password, str):
            password = password.encode('utf-8')
        
        # Generate salt and hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password, salt)
        
        # Return as string
        return hashed.decode('utf-8')
    except Exception as e:
        print(f"⚠️ Password hashing error: {e}")
        raise


# ==================== TOKEN CREATION ====================
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ==================== USER AUTHENTICATION ====================
def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password"""
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


# ==================== GET TOKEN ====================
async def get_token_from_header(credentials: HTTPAuthorizationCredentials = Depends(http_bearer)) -> str:
    """Extract token from Authorization header"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


# ==================== GET CURRENT USER ====================
async def get_current_user(
    token: str = Depends(get_token_from_header),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        print(f"🔍 Decoding token: {token[:30]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"✅ Token payload: {payload}")
        
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            print("❌ User ID is None")
            raise credentials_exception
        
        user_id: int = int(user_id_str)
        print(f"👤 User ID from token: {user_id}")
            
    except JWTError as e:
        print(f"❌ JWT Error: {e}")
        raise credentials_exception
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    print(f"🔎 User found: {user}")
    
    if user is None:
        print("❌ User not found in database")
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user


# ==================== ADMIN REQUIRED ====================
async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require admin role"""
    
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user


# ==================== ENCRYPTION (for API keys) ====================
from cryptography.fernet import Fernet

# Get encryption key from environment or generate a default (for dev only)
# In production, ENCRYPTION_KEY must be set in .env file
encryption_key_str = os.getenv("ENCRYPTION_KEY")
if encryption_key_str:
    ENCRYPTION_KEY = encryption_key_str.encode() if isinstance(encryption_key_str, str) else encryption_key_str
else:
    # Generate a consistent key for development (WARNING: not for production)
    print("⚠️  WARNING: ENCRYPTION_KEY not set in environment. Using generated key (development only)")
    ENCRYPTION_KEY = Fernet.generate_key()

cipher_suite = Fernet(ENCRYPTION_KEY)


def encrypt_api_key(api_key: str) -> str:
    """Encrypt API key for secure storage"""
    return cipher_suite.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt API key"""
    return cipher_suite.decrypt(encrypted_key.encode()).decode()
