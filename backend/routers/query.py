from fastapi import APIRouter, HTTPException
import query_engine
from schemas.query import QueryRequest, SuggestionsRequest

router = APIRouter(tags=["query"])

import json
import queue
import threading
from fastapi.responses import StreamingResponse

@router.post("/query")
async def query_data(request: QueryRequest):
    result_queue = queue.Queue()

    def run_query():
        for chunk in query_engine.execute_query_stream(request.session_id, request.question):
            result_queue.put(chunk)
        result_queue.put(None)  # sentinel to signal completion

    thread = threading.Thread(target=run_query, daemon=True)
    thread.start()

    def event_generator():
        import time
        while True:
            try:
                chunk = result_queue.get(timeout=15)
                if chunk is None:
                    break  # stream complete
                yield f"data: {json.dumps(chunk)}\n\n"
            except queue.Empty:
                # Send a keepalive comment to prevent Render's proxy from closing the connection
                yield ": keepalive\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"})

@router.post("/generate-suggestions")
async def generate_suggestions(request: SuggestionsRequest):
    try:
        suggestions = query_engine.generate_suggestions(request.session_id)
        return {"suggestions": suggestions}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not generate suggestions: {str(e)}")