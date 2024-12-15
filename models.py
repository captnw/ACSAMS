from typing import Annotated, Optional
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
  name: str = Field(...)
  endpoint: API_Endpoint_Enum = Field(...)
  description: str = Field(...)

class UpdateAPIPermission(BaseModel):
  name: str = Field(...)
  endpoint: API_Endpoint_Enum = Field(...)
  description: str = Field(...)