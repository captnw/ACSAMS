import logging
from fastapi.security import OAuth2PasswordBearer   
from passlib.context import CryptContext
from pydantic import ValidationError  
from config import ALGORITHM, SECRET_KEY
from models import User  
from jose import JWTError, jwt  
from datetime import datetime, timedelta, timezone
from typing import Annotated, Union  
from fastapi import Depends, HTTPException, status

from mongo_driver import get_user_by_name_from_MongoDB

"""
auth.py

Responsible for Role base access control with JWT
"""

# Global variables
# Initialize logger (use the logger instead of print for debugging)
logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.DEBUG)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  

refresh_tokens = set()

async def authenticate_user(username: str, password: str) -> Union[User, bool]:   
    """
    Authenticate a user against the MongoDB database
    """
    user = await get_user_by_name_from_MongoDB(username)  
    if not user:  
        return False  
    
    logger.debug(f"Checking password for user: {username}")

    if user.password != password:
        logger.error(f"Password mismatch")
        return False
    logger.debug(f"Password matches")
    return user  

def create_token(data: dict, expires_delta: timedelta = timedelta(minutes=15)):
    """
    Helper method used for creating the accessa and refresh token
    """
    to_encode = data.copy()  
    expire = datetime.now(timezone.utc) + expires_delta  
    to_encode.update({"exp": expire})  
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):  
    """
    Get the current user that is signed in via FastAPI's OAuth2PasswordBearer
    """
    credentials_exception = HTTPException(  
        status_code=status.HTTP_401_UNAUTHORIZED,  
        detail="Could not validate credentials",  
        headers={"WWW-Authenticate": "Bearer"},  
    )  
    try:  
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  
        username: str = payload.get("sub")  
        if username is None:  
            raise credentials_exception  
    except JWTError:  
        raise credentials_exception  
    user = await get_user_by_name_from_MongoDB(username)  
    if user is None:  
        raise credentials_exception  
    return user  

class CheckedRoleIs:  
    """
    Checks if a user is part of the allowed roles, return True if this is case, False otherwise

    Responsible for protecting an endpoint.
    """
    def __init__(self, allowed_roles):  
        self.allowed_roles = allowed_roles  

    def __call__(self, user: Annotated[User, Depends(get_current_user)]):  
        """
        Allows this class to be called like a method, so Depends will work for this class and we can create a protected endpoint
        """
        if user.role in self.allowed_roles:  
            return True  
        raise HTTPException(  
            status_code=status.HTTP_401_UNAUTHORIZED,   
            detail="You don't have enough permissions")  
  
async def validate_refresh_token(token: Annotated[str, Depends(oauth2_scheme)]):  
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")  
    try:  
        #logger.debug(f"this is token {token}")
        #logger.debug(f"this is refresh token {refresh_tokens}")

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  
        logger.debug(f"payload {payload}")
        username: str = payload.get("sub")  
        role: str = payload.get("role")  
        if username is None or role is None:  
            logger.debug(f"user {username} or role {role} is none")
            raise credentials_exception 
    except (JWTError, ValidationError):  
        logger.debug(f"some weird error???")
        raise credentials_exception  
  
    user = await get_user_by_name_from_MongoDB(username)  
  
    if user is None:  
        raise credentials_exception  
  
    return user, token  