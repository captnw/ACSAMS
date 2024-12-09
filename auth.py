import logging
from fastapi.security import OAuth2PasswordBearer   
from passlib.context import CryptContext
from pydantic import ValidationError  
from config import ALGORITHM, SECRET_KEY
from models import User  
from jose import JWTError, jwt  
from datetime import datetime, timedelta, timezone  
from data import refresh_tokens, fake_users_db
from typing import Annotated, Union  
from fastapi import Depends, HTTPException, status

# Global variables
# Initialize logger (use the logger instead of print for debugging)
logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.DEBUG)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  

def get_user(db, username: str) -> Union[User,None]:  
    """
    Given a db and a username, fetches user information from the db and return a 
    """
    for user in db:
        if username in user["username"]:  
            return User(**user)  
  
def authenticate_user(fake_db, username: str, password: str):   
    """
    Authenticate a user against a database
    """
    user = get_user(fake_db, username)  
    if not user:  
        return False  
    
    print("Password check would be here",username,password,user.hashed_password)

    #if not pwd_context.verify(plain_password, hashed_password):  
    #    return False  
    return user  

def create_token(data: dict, expires_delta: timedelta = timedelta(minutes=15)):  
    to_encode = data.copy()  
    expire = datetime.now(timezone.utc) + expires_delta  
    to_encode.update({"exp": expire})  
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):  
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
    user = get_user(fake_users_db, username=username)  
    if user is None:  
        raise credentials_exception  
    return user  
  
async def get_current_active_user( current_user: Annotated[User, Depends(get_current_user)]):
    return current_user  

class RoleChecker:  
    """
    Checks if a user is part of the allowed roles, return True if this is case, False otherwise
    """
    def __init__(self, allowed_roles):  
        self.allowed_roles = allowed_roles  

    def __call__(self, user: Annotated[User, Depends(get_current_active_user)]):  
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
  
    user = get_user(fake_users_db, username=username)  
  
    if user is None:  
        raise credentials_exception  
  
    return user, token  