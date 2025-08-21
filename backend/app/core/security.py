from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone

# user authentication, password management, and JWT (JSON Web Token) generation

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-key" # used in the create_access_token function to sign and encode JWT tokens
ALGORITHM = "HS256" # algorithm used to sign and verify JWT tokens

def hash_password(password: str) -> str: 
    return pwd_context.hash(password)
# hashes user passwords using bcrypt 

def verify_password(plain_password, hashed_password): 
    return pwd_context.verify(plain_password, hashed_password)
# Verifies a plain text password against a stored hash

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=72)):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
# Creates JWT tokens for authenticated users
# Default expiration: 72 hours (3 days)
# Tokens contain user data and expiration time
# Used for maintaining user sessions
