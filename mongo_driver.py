import logging
from typing import Union
import motor.motor_asyncio  
from bson import ObjectId
from config import MONGODB_DATABASE, MONGODB_URL
from models import User, APIPermission
from fastapi import HTTPException

# Initialize logger (use the logger instead of print for debugging)
logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.DEBUG)

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.get_database(MONGODB_DATABASE)

USERS_COLLECTION = "users"
PERMISSIONS_COLLECTION = "permissions"
PLANS_COLLECTION = "plans"

user_collection = db.get_collection(USERS_COLLECTION)
permissions_collection = db.get_collection(PERMISSIONS_COLLECTION)
plans_collection = db.get_collection(PLANS_COLLECTION)

async def get_user_from_MongoDB(username: str) -> Union[User,None]:  
    """
    Given a username, fetches user information from the db and return a User or None if username doesn't exist
    """
    results = await user_collection.find_one({"username":username})
    if results is None:
        return
    return User(**results)

async def add_permission_to_MongoDB(permission: APIPermission):
    """
    Add the APIPermission to MongoDB
    """
    # check if API already exists
    existing_API = await permissions_collection.find_one({"endpoint":permission.endpoint.value})
    if existing_API:
        raise HTTPException(status_code=400, detail=f"Endpoint {permission} already exists in a permission")

    # otherwise just create the permission
    permission_dump = permission.model_dump()
    await permissions_collection.insert_one(permission_dump)

async def get_permission_from_MongoDB(name: str) -> Union[APIPermission, None]:
    """
    Given a permission name, fetches APIPermission information from the db and return a APIPermission or None if the permission name doesn't exist
    """
    permission = await permissions_collection.find_one({"name": name})
    if permission is None:
        return
    return APIPermission(**permission)