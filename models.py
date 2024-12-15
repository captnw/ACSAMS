from typing import Annotated, Dict, Optional
from pydantic import BaseModel, BeforeValidator, Field
from plans import API_Endpoint_Enum

# Define all models to be used in MongoDB

# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]

class User(BaseModel): 
  """
  User will need to be signed in to use this API
  """ 
  id: Optional[PyObjectId] = Field(alias="_id", default=None)
  username: str = Field(...)
  role: str = Field(...)
  password: str = Field(...) # This is a simple application, you can go hash this yourself
  
class Token(BaseModel):
  """
  Used with FastAPI's OAuth2PasswordRequestForm 
  """
  access_token: str = Field(...) 
  refresh_token: str = Field(...)

class APIPermission(BaseModel):
  id: Optional[PyObjectId] = Field(alias="_id", default=None)
  name: str = Field(default="RandomAPI1", validate_default=True)
  endpoint: API_Endpoint_Enum = Field(default=API_Endpoint_Enum.random1, validate_default=True)
  description: str = Field(default="RandomAPI1 description", validate_default=True)

class UpdateAPIPermission(BaseModel):
  name: str = Field(default="RandomAPI1", validate_default=True)
  endpoint: API_Endpoint_Enum = Field(default=API_Endpoint_Enum.random1, validate_default=True)
  description: str = Field(default="RandomAPI1 description", validate_default=True)

class APIPlan(BaseModel):
  id: Optional[PyObjectId] = Field(alias="_id", default=None)
  name: str = Field(default="RandomAPIPlan1", validate_default=True)
  apilimit : Dict[PyObjectId, Annotated[int, Field(gt=0)]] = Field(default={"permissionId":10}, validate_default=True)

class UpdateAPIPlan(BaseModel):
  name: str = Field(default="RandomAPIPlan1", validate_default=True)
  apilimit : Dict[PyObjectId, Annotated[int, Field(gt=0)]] = Field(default={"permissionId":10}, validate_default=True)