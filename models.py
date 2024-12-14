from pydantic import BaseModel, Field  
from plans import API_Endpoint_Enum

# Define all models to be used in MongoDB

class User(BaseModel): 
  """
  User will need to be signed in to use this API
  """ 
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
  name: str = Field(...)
  endpoint: API_Endpoint_Enum = Field(...)
  description: str = Field(...)