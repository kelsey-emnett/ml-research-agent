from pydantic import BaseModel, Field
import uuid
from datetime import datetime


class ChatRequest(BaseModel):
    system_message: str
    user_message: str


class ChatResponse(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    response: str
