from fastapi import APIRouter, UploadFile, File, HTTPException
import data_loader

router = APIRouter(prefix="/api", tags=["upload"])

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        result = data_loader.process_file(contents, file.filename)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
