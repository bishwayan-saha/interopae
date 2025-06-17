from pydantic import BaseModel, Field


class UserPrompt(BaseModel):
    message: str = Field(..., description="User query to the application")
    role: str = Field(..., description="user or AI")


class UserRequest(BaseModel):
    request: list[UserPrompt]
