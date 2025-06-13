from pydantic import BaseModel, Field

class UserRequest(BaseModel):
    query: str = Field(..., description="User query to the application")