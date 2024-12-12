from datetime import timedelta
import logging
from typing import Annotated 

from fastapi import Depends, FastAPI, HTTPException  
from fastapi.security import OAuth2PasswordRequestForm
  
from auth import create_token, authenticate_user, CheckedRoleIs, validate_refresh_token, refresh_tokens
from models import User, Token  
from config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_MINUTES

# Initialize logger (use the logger instead of print for debugging)
logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.DEBUG)

app = FastAPI(
    title="Cloud Service Access Management System API",
    summary="A backend system for managing access to cloud services based on user subscriptions. \n\
        Role-based access control (RBAC) system where the admin can modify user permissions and subscription plans \n\
            Simulate cloud service usage and enforce limits based on subscription plans",
)

access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  
refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)  

@app.get("/hello")  
def hello_func():  
  """
  Example FASTAPI endpoint #1
  """
  return "Hello World"  
  
@app.get("/data")  
def get_data():  
  """
  Example FASTAPI endpoint #2
  """
  return {"data": "This is important data"} 

@app.get("/realdata")  
def get_real_data(_: Annotated[bool, Depends(CheckedRoleIs(allowed_roles=["admin"]))]):  
  """
  Example FASTAPI endpoint with authentication, you need to sign in with admin user before interacting with API
  """
  return {"data": "This is REALLY important data"}

@app.post("/token")  
async def login_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:  
  """
  Login with username and password to receive an access and refresh token
  """
  user = await authenticate_user(form_data.username, form_data.password)  
  if not user:  
    raise HTTPException(status_code=400, detail="Incorrect username or password")  
  
  access_token = create_token(data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires)  
  refresh_token = create_token(data={"sub": user.username, "role": user.role}, expires_delta=refresh_token_expires)  
  refresh_tokens.add(refresh_token)  

  logger.debug(f'did we add access token {access_token}')
  logger.debug(f'did we add refresh token {refresh_tokens}')
  return Token(access_token=access_token, refresh_token=refresh_token)  

@app.post("/refresh")  
async def refresh_access_token(token_data: Annotated[tuple[User, str], Depends(validate_refresh_token)]):  
  """
  Request our refresh token to get a new access token when the access token expires
  """
  user, token = token_data  
  access_token = create_token(data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires)  
  refresh_token = create_token(data={"sub": user.username, "role": user.role}, expires_delta=refresh_token_expires)  

  try:
    refresh_tokens.remove(token)  
  except KeyError:
    pass

  refresh_tokens.add(refresh_token)  
  return Token(access_token=access_token, refresh_token=refresh_token)

# Random APIs

@app.get("/random1")  
def get_random_1():  
  """
  The 1st random API
  """
  return "Random 1"

@app.get("/random2")  
def get_random_2():  
  """
  The 2nd random API
  """
  return "Random 2"

@app.get("/random3")  
def get_random_3():  
  """
  The 3rd random API
  """
  return "Random 3"

@app.get("/random4")  
def get_random_4():  
  """
  The 4th random API
  """
  return "Random 4"

@app.get("/random5")  
def get_random_5():  
  """
  The 5th random API
  """
  return "Random 5"

@app.get("/random6")  
def get_random_6():  
  """
  The 6th random API
  """
  return "Random 6"