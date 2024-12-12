from pydantic import BaseModel  
  
class User(BaseModel):  
  username: str | None = None
  role: str | None = None
  password: str | None = None # This is a simple application, you can go hash this yourself
  
class Token(BaseModel):  
  access_token: str | None = None  
  refresh_token: str | None = None