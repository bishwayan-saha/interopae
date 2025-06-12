from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class StatusMessage(Enum):
    OK = "OK"
    ERROR = "ERROR"


class ServerResponse(BaseModel):
    data: Any = Field(
        ...,
        description="Server response, can be list, dictionary or primitive data types",
    )
    status: StatusMessage = Field(..., description="HTTP response status message")
    message: str = Field(
        ..., description="general message representing server response"
    )
    timestamp: str = Field(
        default=datetime.now().__str__(), description="current timestamp for tracking"
    )

    class Config:
        use_enum_values = True

