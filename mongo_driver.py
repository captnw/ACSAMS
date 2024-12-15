import logging
from typing import Union
import motor.motor_asyncio  
from bson import ObjectId
from config import MONGODB_DATABASE, MONGODB_URL
from models import APIPlan, UpdateAPIPermission, UpdateAPIPlan, User, APIPermission
from fastapi import HTTPException, Response, status
from pymongo import ReturnDocument

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

# Design goal:
# Essentially if an object B is dependent on object A; then prevent all changes (modify/delete) to object A until the dependency between B and A is removed

# User methods

async def get_user_by_name_from_MongoDB(username: str) -> Union[User,None]:  
    """
    Given a username, fetches user information from the db and return a User or None if username doesn't exist
    """
    results = await user_collection.find_one({"username":username})
    if results is None:
        return
    return User(**results)

async def get_user_by_id_from_MongoDB(id: str) -> Union[User,None]:  
    """
    Given a username, fetches user information from the db and return a User or None if username doesn't exist
    """
    results = await user_collection.find_one({"_id": ObjectId(id)})
    if results is None:
        return
    return User(**results)

# Permission methods

async def add_permission_to_MongoDB(permission: APIPermission):
    """
    Add the APIPermission to MongoDB
    """
    # check if API already exists
    existing_API = await permissions_collection.find_one({"endpoint":permission.endpoint.value})
    if existing_API:
        raise HTTPException(status_code=400, detail=f"Endpoint {permission} already exists in a permission")
    
    # otherwise just create the permission
    permission_dump = permission.model_dump(by_alias=True, exclude=["id"])
    await permissions_collection.insert_one(permission_dump)

async def modify_permission_to_MongoDB(id : str, permission: UpdateAPIPermission):
    """
    Modify the APIPermission to MongoDB
    """
    # check if ID already exists
    existing_permission = await permissions_collection.find_one({"_id":ObjectId(id)})
    if not existing_permission:
        raise HTTPException(status_code=400, detail=f"No permission with object id {existing_permission} exist")
    
    # check if permission is being used by any existing plan and stop update if it is being used
    used_by_existing_plan = await plans_collection.find_one({ f"apilimit.{ObjectId(id)}": {"$exists": True}})
    if used_by_existing_plan:
        existing_plan = APIPlan(**used_by_existing_plan)
        raise HTTPException(status_code=400, detail=f"Permission with object id {existing_permission} exist and is used in plan {existing_plan.id}")

    old_permission = APIPermission(**existing_permission)

    if old_permission.endpoint.value != permission.endpoint.value:
        # There is a change to the endpoint value
        # We need to check if the new endpoint isn't being used by some existing permission
        # Simple check: count the number of permissions with endpoint as the new endpoint and ensure it is 0
        existing_API = await permissions_collection.find_one({"endpoint":permission.endpoint.value})
        if existing_API:
            raise HTTPException(status_code=400, detail=f"Endpoint {permission} already exists in a permission")
    
    permission = {
        k : v for k, v in permission.model_dump(by_alias=True).items() if v is not None
    }

    # ok to update current
    update_result = await permissions_collection.find_one_and_update(
        {"_id": ObjectId(id)},
        {"$set": permission},
        return_document=ReturnDocument.AFTER
    )

    if update_result is None:
        raise HTTPException(status_code=500, detail=f"Unable to update permission with id {id} with new values {permission}")

async def delete_permission_in_MongoDB(id : str):
    """
    Delete the APIPermission in MongoDB
    """
    delete_result = await permissions_collection.delete_one({"_id": ObjectId(id)})

    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"API Permission {id} not found")

    # add check to prevent deleting permission IF it is in use by a plan

async def get_permission_from_MongoDB(name: str) -> Union[APIPermission, None]:
    """
    Given a permission name, fetches APIPermission information from the db and return a APIPermission or None if the permission name doesn't exist
    """
    permission = await permissions_collection.find_one({"name": name})
    if permission is None:
        return
    return APIPermission(**permission)

# Plan methods

async def add_plan_to_MongoDB(plan: APIPlan):
    """
    Add the APIPlan to MongoDB
    """
    # We can have different plans with same set of APIs; so don't do checks

    # If there is no APILimit dict, throw an exception
    if len(plan.apilimit) == 0:
        raise HTTPException(status_code=400, detail=f"Plan {plan} need to have APILimit dict")

    # double check API already exists, otherwise raise exception
    for permission_id in plan.apilimit.keys():
        permission = await permissions_collection.find_one({"_id":ObjectId(permission_id)})
        if not permission:
            raise HTTPException(status_code=400, detail=f"Permission with id {permission_id} doesn't exist; so cannot be attached to plan")
    
    # otherwise just create the plan
    plan_dump = plan.model_dump(by_alias=True, exclude=["id"])
    await plans_collection.insert_one(plan_dump)

async def modify_plan_to_MongoDB(id : str, plan: UpdateAPIPlan):
    """
    Modify the APIPermission to MongoDB
    """
    # check if ID already exists
    existing_plan = await plans_collection.find_one({"_id":ObjectId(id)})
    if not existing_plan:
        raise HTTPException(status_code=400, detail=f"No plan with object id {existing_plan} exist")
    
    # check if plan is being used by any user, if it is; then stop the update (TODO: WORK IN PROGRESS)
    # prevent deleting/modifying plan if it is in use by a customer (TODO: WORK IN PROGRESS)

    # double check API already exists, otherwise raise exception
    for permission_id in plan.apilimit.keys():
        permission = await permissions_collection.find_one({"_id":ObjectId(permission_id)})
        if not permission:
            raise HTTPException(status_code=400, detail=f"Permission with id {permission_id} doesn't exist; so cannot be attached to plan")

    plan = {
        k : v for k, v in plan.model_dump(by_alias=True).items() if v is not None
    }

    # ok to update current
    update_result = await plans_collection.find_one_and_update(
        {"_id": ObjectId(id)},
        {"$set": plan},
        return_document=ReturnDocument.AFTER
    )

    if update_result is None:
        raise HTTPException(status_code=500, detail=f"Unable to update plan with id {id} with new values {plan}")
