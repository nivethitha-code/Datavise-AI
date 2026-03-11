from fastapi import APIRouter, HTTPException
import query_engine
from schemas.query import QueryRequest, SuggestionsRequest

router = APIRouter(tags=["query"])

import json
from fastapi.responses import StreamingResponse

@router.post("/query")
async def query_data(request: QueryRequest):
    def event_generator():
        for chunk in query_engine.execute_query_stream(request.session_id, request.question):
            # Yield as valid SSE or just raw JSON lines
            yield f"data: {json.dumps(chunk)}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/generate-suggestions")
async def generate_suggestions(request: SuggestionsRequest):
    try:
        suggestions = query_engine.generate_suggestions(request.session_id)
        return {"suggestions": suggestions}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not generate suggestions: {str(e)}")