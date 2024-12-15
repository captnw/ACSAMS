from datetime import timedelta
import logging
from typing import Annotated 

from fastapi import Depends, FastAPI, HTTPException, Body, status
from fastapi.security import OAuth2PasswordRequestForm
  
from auth import create_token, authenticate_user, CheckedRoleIs, validate_refresh_token, refresh_tokens
from models import APIPermission, APIPlan, UpdateAPIPermission, UpdateAPIPlan, User, Token  
from config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_MINUTES
from mongo_driver import add_permission_to_MongoDB, add_plan_to_MongoDB, delete_permission_in_MongoDB, modify_permission_to_MongoDB, modify_plan_to_MongoDB
from bson import ObjectId

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

# Test endpoints (just to test RBAC)
@app.get("/hello")  
def hello_func():  
  """
  Example FASTAPI endpoint #1
  """
  return "Hello World, you can access this without signing in"  

@app.get("/data")  
def get_data(_: Annotated[bool, Depends(CheckedRoleIs(allowed_roles=["user"]))]):  
  """
  Example FASTAPI endpoint #2
  """
  return {"data": "This is important data, need to sign in with a user role"} 

@app.get("/realdata")  
def get_real_data(_: Annotated[bool, Depends(CheckedRoleIs(allowed_roles=["admin"]))]):  
  """
  Example FASTAPI endpoint with authentication, you need to sign in with admin user before interacting with API
  """
  return {"data": "This is REALLY important data, need to sign in with an admin role"}

@app.post("/token",response_description="Login with username and password and get access and refresh tokens")  
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

@app.post("/refresh",response_description="Get new access token when access token expires and when logged in")  
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

# Permissions

@app.post("/permissions",
          response_description="Add API permission",
          status_code=status.HTTP_201_CREATED)
async def add_permission(_: Annotated[bool, Depends(CheckedRoleIs(allowed_roles=["admin"]))], permission : APIPermission = Body(...)):
  """
  Insert a new API permission
  """
  await add_permission_to_MongoDB(permission)
  return f"Created API {permission}"

@app.put("/permissions/{permissionId}",
          response_description="Modify API permission",
          status_code=status.HTTP_200_OK)
async def modify_permission(permissionId : str, _ : Annotated[bool, Depends(CheckedRoleIs(allowed_roles=["admin"]))] = Body(...), permission : UpdateAPIPermission = Body(...)):
  """
  Update an existing API permission
  """
  await modify_permission_to_MongoDB(permissionId, permission)
  return f"Updated API {permission}"

@app.delete("/permissions/{permissionId}",
          response_description="Delete API permission",
          status_code=status.HTTP_200_OK)
async def delete_permission(permissionId : str, _ : Annotated[bool, Depends(CheckedRoleIs(allowed_roles=["admin"]))] = Body(...)):
  """
  Update an existing API permission
  """
  await delete_permission_in_MongoDB(permissionId)
  return f"Deleted API {permissionId}"

# Plans
@app.post("/plans",
          response_description="Add plan",
          status_code=status.HTTP_201_CREATED)
async def add_plan(_: Annotated[bool, Depends(CheckedRoleIs(allowed_roles=["admin"]))], plan : APIPlan = Body(...)):
  """
  Insert a new API permission
  """
  logger.debug(plan)
  await add_plan_to_MongoDB(plan)
  return f"Created Plan {plan}"

@app.put("/plans/{planId}",
          response_description="Modify plan",
          status_code=status.HTTP_201_CREATED)
async def modify_plan(planId : str, _: Annotated[bool, Depends(CheckedRoleIs(allowed_roles=["admin"]))], plan : UpdateAPIPlan = Body(...)):
  """
  Insert a new API permission
  """
  logger.debug(plan)
  await modify_plan_to_MongoDB(planId, plan)
  return f"Updated Plan {plan}"

# Random APIs

@app.get("/random1",response_description="GET random endpoint 1")  
def get_random_1():  
  """
  The 1st random API
  """
  return "Random 1"

@app.get("/random2",response_description="GET random endpoint 2")  
def get_random_2():  
  """
  The 2nd random API
  """
  return "Random 2"

@app.get("/random3",response_description="GET random endpoint 3")  
def get_random_3():  
  """
  The 3rd random API
  """
  return "Random 3"

@app.get("/random4",response_description="GET random endpoint 4")  
def get_random_4():  
  """
  The 4th random API
  """
  return "Random 4"

@app.get("/random5",response_description="GET random endpoint 5")  
def get_random_5():  
  """
  The 5th random API
  """
  return "Random 5"

@app.get("/random6",response_description="GET random endpoint 6")  
def get_random_6():  
  """
  The 6th random API
  """
  return "Random 6"