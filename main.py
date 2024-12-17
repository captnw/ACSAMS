from datetime import timedelta
import logging
from typing import Annotated 

from fastapi import Depends, FastAPI, HTTPException, Body, status
from fastapi.security import OAuth2PasswordRequestForm
  
from auth import create_token, authenticate_user, CheckedRoleIs, get_current_user, validate_refresh_token, refresh_tokens
from models import APIPermission, APIPlan, UpdateAPIPermission, UpdateAPIPlan, User, Token  
from config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_MINUTES
from mongo_driver import add_permission_to_MongoDB, add_plan_to_MongoDB, delete_permission_in_MongoDB, delete_plan_in_MongoDB, modify_permission_to_MongoDB, modify_plan_to_MongoDB, subscribe_to_plan_in_MongoDB
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

# RBAC demonstration endpoints
@app.get("/publiconly")  
def public_only():  
  """
  Endpoint that can be accessed by everyone
  """
  return "This endpoint can be used by everyone"  

@app.get("/useronly")  
def user_only(_: Annotated[bool, Depends(CheckedRoleIs(allowed_roles=["user"]))]):  
  """
  Endpoint that can be accessed by users
  """
  return {"data": "This is important data, need to sign in with a user role"} 

@app.get("/adminonly")  
def admin_only(_: Annotated[bool, Depends(CheckedRoleIs(allowed_roles=["admin"]))]):  
  """
  Endpoint that can be accessed by admin
  """
  return {"data": "This is REALLY important data, need to sign in with an admin role"}

@app.get("/useroradmin")  
def user_or_admin(_: Annotated[bool, Depends(CheckedRoleIs(allowed_roles=["user","admin"]))]):  
  """
  Endpoint that can be accessed by users OR admins
  """
  return {"data": "This is semi important data, need to sign in with an user or admin role"}

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

# Permissions endpoints

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

# Plans endpoints

@app.post("/plans",
          response_description="Add plan",
          status_code=status.HTTP_201_CREATED)
async def add_plan(_: Annotated[bool, Depends(CheckedRoleIs(allowed_roles=["admin"]))], plan : APIPlan = Body(...)):
  """
  Insert a new API permission
  """
  await add_plan_to_MongoDB(plan)
  return f"Created Plan {plan}"

@app.put("/plans/{planId}",
          response_description="Modify plan",
          status_code=status.HTTP_200_OK)
async def modify_plan(planId : str, _: Annotated[bool, Depends(CheckedRoleIs(allowed_roles=["admin"]))], plan : UpdateAPIPlan = Body(...)):
  """
  Insert a new API permission
  """
  await modify_plan_to_MongoDB(planId, plan)
  return f"Updated Plan {plan}"

@app.delete("/plans/{planId}",
          response_description="Delete plan",
          status_code=status.HTTP_200_OK)
async def delete_plan(planId : str, _: Annotated[bool, Depends(CheckedRoleIs(allowed_roles=["admin"]))]):
  """
  Insert a new API permission
  """
  await delete_plan_in_MongoDB(planId)
  return f"Deleted Plan {planId}"

@app.post("/subscriptions/",
          response_description="Subscribed to plan (as a user)",
          status_code=status.HTTP_200_OK)
async def subscribe_plan(planId : str, _: Annotated[bool, Depends(CheckedRoleIs(allowed_roles=["user"]))], current_user: Annotated[User, Depends(get_current_user)]):
  """
  Subscribe to a plan as a user
  """
  await subscribe_to_plan_in_MongoDB(planId, current_user)
  return f"User {current_user} subscribed to plan {planId}"

# Random APIs (these don't do anything other than be monitored for usage)

@app.get("/random1",response_description="GET random endpoint 1")  
def get_random_1(_: Annotated[bool, Depends(CheckedRoleIs(allowed_roles=["user"]))]):  
  """
  The 1st random API (users only)
  """
  return "Random 1"

@app.get("/random2",response_description="GET random endpoint 2")  
def get_random_2(_: Annotated[bool, Depends(CheckedRoleIs(allowed_roles=["user"]))]):  
  """
  The 2nd random API (users only)
  """
  return "Random 2"

@app.get("/random3",response_description="GET random endpoint 3")  
def get_random_3(_: Annotated[bool, Depends(CheckedRoleIs(allowed_roles=["user"]))]):  
  """
  The 3rd random API (users only)
  """
  return "Random 3"

@app.get("/random4",response_description="GET random endpoint 4")  
def get_random_4(_: Annotated[bool, Depends(CheckedRoleIs(allowed_roles=["user"]))]):  
  """
  The 4th random API (users only)
  """
  return "Random 4"

@app.get("/random5",response_description="GET random endpoint 5")  
def get_random_5(_: Annotated[bool, Depends(CheckedRoleIs(allowed_roles=["user"]))]):  
  """
  The 5th random API (users only)
  """
  return "Random 5"

@app.get("/random6",response_description="GET random endpoint 6")  
def get_random_6(_: Annotated[bool, Depends(CheckedRoleIs(allowed_roles=["user"]))]):  
  """
  The 6th random API (users only)
  """
  return "Random 6"