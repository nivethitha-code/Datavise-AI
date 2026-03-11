from pydantic import BaseModel

class SessionRestoreResponse(BaseModel):
    session_id: str
    profile: dict
    preview: list