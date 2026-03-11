from fastapi import APIRouter, HTTPException
import query_engine
from schemas.query import QueryRequest, SuggestionsRequest

router = APIRouter(prefix="/api", tags=["query"])

@router.post("/query")
async def query_data(request: QueryRequest):
    try:
        result = query_engine.execute_query(request.session_id, request.question)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/generate-suggestions")
async def generate_suggestions(request: SuggestionsRequest):
    try:
        suggestions = query_engine.generate_suggestions(request.session_id)
        return {"suggestions": suggestions}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not generate suggestions: {str(e)}")
