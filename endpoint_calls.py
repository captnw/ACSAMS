# This module is responsible for the class that protects endpoints depending on user has a valid plan, access to the endpoint, and still has enough calls

import logging
from typing import Annotated

from fastapi import Depends, HTTPException
from auth import get_current_user
from endpoint import API_Endpoint_Enum
from models import User
from mongo_driver import get_permission_by_endpoint_from_MongoDB, get_plan_by_id_MongoDB

logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.DEBUG)

class UserHasPermission:  
    """
    Checks if a user is subscribed to plan that has access to the endpoint, return True if this is case, False otherwise

    Responsible for protecting an endpoint from users without subscriptions.
    """
    def __init__(self, endpoint):  
        self.endpoint = API_Endpoint_Enum(endpoint)  

    async def __call__(self, user: Annotated[User, Depends(get_current_user)]):  
        """
        Allows this class to be called like a method, so Depends will work for this class and we can check if the user has access to endpoint
        """
        perm = await get_permission_by_endpoint_from_MongoDB(self.endpoint)
        
        # check for access
        if (not user.subscribed_plan_id or not user.current_api_usage):
            raise HTTPException(status_code=400, detail=f"User is not subscribed to a plan")
        
        logger.debug(perm.id)
        logger.debug(user.current_api_usage)

        if not (perm.id in user.current_api_usage):
            raise HTTPException(status_code=400, detail=f"Endpoint {perm.endpoint} is not available as per the user's subscribed plan")

        # check to see if we still have enough calls remaining
        current_usage = user.current_api_usage[perm.id]
        current_plan = await get_plan_by_id_MongoDB(user.subscribed_plan_id)

        logger.debug(current_usage)
        logger.debug(current_plan.apilimit[perm.id])

        # do check here 

        # then increment current usage and update the user entry in mongodb

        return True