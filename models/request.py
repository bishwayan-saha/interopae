from pydantic import BaseModel, Field

class UserRequest(BaseModel):
    message: str = Field(..., description="User query to the application")