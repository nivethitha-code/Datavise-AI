from pydantic import BaseModel
from datetime import datetime
from typing import List

class ChatMessage(BaseModel):
    role: str
    content: str
    created_at: datetime | None = None

class HistoryResponse(BaseModel):
    messages: List[ChatMessage]
