import logging
from typing import Union
import motor.motor_asyncio  
from bson import ObjectId
from config import MONGODB_DATABASE, MONGODB_URL
from models import User

# Initialize logger (use the logger instead of print for debugging)
logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.DEBUG)

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.get_database(MONGODB_DATABASE)

USERS_COLLECTION = "users"

user_collection = db.get_collection(USERS_COLLECTION)

async def get_user_from_MongoDB(username: str) -> Union[User,None]:  
    """
    Given a db and a username, fetches user information from the db and return a User or None if username doesn't exist
    """
    results = await user_collection.find_one({"username":username})
    if results is None:
        return
    return User(**results)