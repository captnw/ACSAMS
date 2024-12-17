import logging
from typing import Union
import motor.motor_asyncio  
from bson import ObjectId
from bson.errors import InvalidId
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

def trycastobjectId(id) -> Union[ObjectId,None]:
    """
    Exception wrapper that handles casting an id into an ObjectId
    """
    object_id : Union[ObjectId,None] = None
    try:
        object_id = ObjectId(id)
        return object_id
    except InvalidId as e:
        logger.exception(e)
        raise HTTPException(status_code=400, detail=str(e)) # makes this pretty looking on SwaggerAPI and gives a descriptive response

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
    results = await user_collection.find_one({"_id": trycastobjectId(id)})
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
    existing_permission = await permissions_collection.find_one({"_id":trycastobjectId(id)})
    if not existing_permission:
        raise HTTPException(status_code=400, detail=f"No permission with object id {existing_permission} exist")
    
    # check if permission is being used by any existing plan and stop update if it is being used
    used_by_existing_plan = await plans_collection.find_one({ f"apilimit.{trycastobjectId(id)}": {"$exists": True}})
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
        {"_id": trycastobjectId(id)},
        {"$set": permission},
        return_document=ReturnDocument.AFTER
    )

    if update_result is None:
        raise HTTPException(status_code=500, detail=f"Unable to update permission with id {id} with new values {permission}")

async def delete_permission_in_MongoDB(id : str):
    """
    Delete the APIPermission in MongoDB
    """
    # check if permission is being used by any existing plan and stop update if it is being used
    used_by_existing_plan = await plans_collection.find_one({ f"apilimit.{trycastobjectId(id)}": {"$exists": True}})
    if used_by_existing_plan:
        existing_plan = APIPlan(**used_by_existing_plan)
        raise HTTPException(status_code=400, detail=f"Permission with object id {id} exist and is used in plan {existing_plan.id}")

    delete_result = await permissions_collection.delete_one({"_id": trycastobjectId(id)})

    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"API Permission {id} not found")

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
        permission = await permissions_collection.find_one({"_id":trycastobjectId(permission_id)})
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
    existing_plan = await plans_collection.find_one({"_id":trycastobjectId(id)})
    if not existing_plan:
        raise HTTPException(status_code=400, detail=f"No plan with object id {existing_plan} exist")
    
    # check if plan is being used by any user, if it is; then stop the update
    used_by_existing_user = await user_collection.find_one({ f"subscribed_plan_id": f"{id}"})
    if used_by_existing_user:
        existing_user = User(**used_by_existing_user)
        raise HTTPException(status_code=400, detail=f"Plan with object id {id} exist and is subscribed to by at least one user (user with id {existing_user.id}...)")
    
    # double check API already exists, otherwise raise exception
    for permission_id in plan.apilimit.keys():
        permission = await permissions_collection.find_one({"_id":trycastobjectId(permission_id)})
        if not permission:
            raise HTTPException(status_code=400, detail=f"Permission with id {permission_id} doesn't exist; so cannot be attached to plan")

    plan = {
        k : v for k, v in plan.model_dump(by_alias=True).items() if v is not None
    }

    # ok to update current
    update_result = await plans_collection.find_one_and_update(
        {"_id": trycastobjectId(id)},
        {"$set": plan},
        return_document=ReturnDocument.AFTER
    )

    if update_result is None:
        raise HTTPException(status_code=500, detail=f"Unable to update plan with id {id} with new values {plan}")

async def delete_plan_in_MongoDB(id : str):
    """
    Delete the APIPlan in MongoDB
    """
    # check if plan is being used by any existing user and stop update if it is being used (TODO: WORK IN PROGRESS)
    used_by_existing_user = await user_collection.find_one({ f"subscribed_plan_id": f"{id}"})
    if used_by_existing_user:
        existing_user = User(**used_by_existing_user)
        raise HTTPException(status_code=400, detail=f"Plan with object id {id} exist and is subscribed to by at least one user (user with id {existing_user.id}...)")
    
    # do deletion
    delete_result = await plans_collection.delete_one({"_id": trycastobjectId(id)})
    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"API Permission {id} not found")

# User Subscription Handling

async def subscribe_to_plan_in_MongoDB(plan_id : str, user : User):
    """
    Subscribe to plan in MongoDB by updating the user
    """
    # check if plan is valid
    existing_plan = await plans_collection.find_one({"_id":trycastobjectId(plan_id)})
    if not existing_plan:
        raise HTTPException(status_code=400, detail=f"No plan with object id {plan_id} exist")

    # check if user is valid
    user_found_by_id = await get_user_by_id_from_MongoDB(user.id)
    if not user_found_by_id:
        raise HTTPException(status_code=400, detail=f"No user with object id {user.id} exist")
    
    user.subscribed_plan_id = plan_id
    existing_plan = APIPlan(**existing_plan)

    # set the usage to 0
    user.current_api_usage = {plan_id:0 for plan_id,_ in existing_plan.apilimit.items()}

    user_id = user.id
    user = {
        k : v for k, v in user.model_dump(by_alias=True, exclude=["id"]).items() if v is not None
    }

    # ok to update current
    update_result = await user_collection.find_one_and_update(
        {"_id": trycastobjectId(user_id)},
        {"$set": user},
        return_document=ReturnDocument.AFTER
    )

    if update_result is None:
        raise HTTPException(status_code=500, detail=f"Unable to subscribe user with id {user_id} to plan {plan_id}")
    
async def view_plan_details_from_user_in_MongoDB(userId : str) -> str:
    # check if user is valid
    user = await get_user_by_id_from_MongoDB(userId)
    if not user:
        raise HTTPException(status_code=400, detail=f"No user with object id {userId} exist")

    # check if plan is valid
    existing_plan = await plans_collection.find_one({"_id":trycastobjectId(user.subscribed_plan_id)}) if user.subscribed_plan_id else None
    if not existing_plan:
        raise HTTPException(status_code=400, detail=f"No plan with object id {user.subscribed_plan_id} exist")
    plan = APIPlan(**existing_plan)

    output = "User (id: {0}) {1}; role: {2}".format(user.id, user.username, user.role)
    output += "\nSubscribed to plan (id: {0}) {1}".format(user.subscribed_plan_id, plan.name)
    output += "\n~~~~"

    # fetch permission details
    for permission_id, limit in plan.apilimit.items():
        permission = await permissions_collection.find_one({"_id":trycastobjectId(permission_id)})
        if not permission:
            raise HTTPException(status_code=400, detail=f"Permission with id {permission_id} doesn't exist; it should not be in plan {plan.id}")
        perm = APIPermission(**permission)
        output += "\n"
        output += "\nPermission (id: {0}) {1}".format(perm.id,perm.name)
        output += "\nEndpoint: {0} API call limit: {1}".format(perm.endpoint,limit)
        output += "\nDescription: {0}".format(perm.description)
    
    return output