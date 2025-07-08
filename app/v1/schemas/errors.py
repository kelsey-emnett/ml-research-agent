from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from typing import Optional


class ErrorInput(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str
    message: str
    module: Optional[str] = None
    funcName: str
    lineno: int
    pathname: str
