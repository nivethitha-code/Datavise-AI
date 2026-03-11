from fastapi import APIRouter, HTTPException
import numpy as np
import data_loader
import query_engine

router = APIRouter(prefix="/api", tags=["history"])

@router.get("/history/{session_id}")
async def get_history(session_id: str):
    try:
        messages = query_engine.get_history(session_id)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/{session_id}")
async def restore_session(session_id: str):
    """Restores profile + preview data from Supabase for a given session."""
    session = data_loader.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session expired or not found. Please re-upload your file.")

    df = session["df"]
    profile = session["profile"]
    preview_df = df.head(10).replace({np.nan: None})
    preview_data = preview_df.to_dict(orient="records")

    return {
        "session_id": session_id,
        "profile": profile,
        "preview": preview_data,
    }
