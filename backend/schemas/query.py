from pydantic import BaseModel

class QueryRequest(BaseModel):
    session_id: str
    question: str

class SuggestionsRequest(BaseModel):
    session_id: str
