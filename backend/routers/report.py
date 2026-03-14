from fastapi import APIRouter, HTTPException, Response
from services.pdf_generator import generate_session_pdf
import query_engine

router = APIRouter(prefix="/report", tags=["reports"])

@router.get("/export-pdf/{session_id}")
async def export_pdf(session_id: str):
    """Generates and returns a branded PDF report for the chat session."""
    try:
        # 1. Fetch history
        history = query_engine.get_history(session_id) or []
        
        # 2. Generate PDF bytes
        pdf_bytes = generate_session_pdf(session_id, history)
        
        if not pdf_bytes:
             raise HTTPException(status_code=500, detail="Failed to generate PDF.")

        # 3. Return as a streamable response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Datavise_Analysis_{session_id[:8]}.pdf"}
        )

    except HTTPException as he:
        print(f"⚠️  PDF Export blocked: {he.detail}")
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ PDF Export fatal error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")