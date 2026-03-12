from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

from database import init_db, init_storage
from routers import upload_router, query_router, history_router, report_router

# Load environment variables
base_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(base_dir, ".env")
load_dotenv(dotenv_path)

app = FastAPI(title="AI Data Analyst API – Agentic Edition")

# CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
allow_all = "*" in allowed_origins or not any(allowed_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else allowed_origins,
    allow_credentials=False if allow_all else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Lifecycle ────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    """Run database and storage initialization on startup."""
    init_db()
    init_storage()

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/")
def read_root():
    return {"status": "ok", "message": "AI Data Analyst – Agentic Backend is running"}

# ── Routers ───────────────────────────────────────────────────────────────────
# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(upload_router, prefix="/api")
app.include_router(query_router, prefix="/api")
app.include_router(history_router, prefix="/api")
app.include_router(report_router, prefix="/api")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)