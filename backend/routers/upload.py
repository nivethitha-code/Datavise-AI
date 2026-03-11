from fastapi import APIRouter, UploadFile, File, HTTPException
import data_loader

router = APIRouter(tags=["upload"])

from services.dashboard_service import run_automated_analysis

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        result = data_loader.process_file(contents, file.filename)
        
        # Trigger 3-step automated analysis for the Starter Dashboard
        session_id = result.get("session_id")
        if session_id:
            automated_results = run_automated_analysis(session_id)
            result["automated_analysis"] = automated_results
            
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")