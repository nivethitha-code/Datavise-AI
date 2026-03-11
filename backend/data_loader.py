import pandas as pd
import io
import uuid
import numpy as np
import os
from datetime import datetime
from dotenv import load_dotenv
from database import get_supabase

load_dotenv()

# Keep in-memory store for DataFrame (not serializable to DB)
# Supabase stores metadata; the DataFrame itself stays in RAM for speed.
# If the server restarts or session is missing, we reload from Supabase Storage.
_memory_store: dict = {}

def process_file(file_content: bytes, filename: str) -> dict:
    """
    1. Parse and clean the file
    2. Upload the raw file to Supabase Storage (for persistence)
    3. Save session + profile to Supabase DB
    4. Return session_id, profile, preview
    """
    # ── 1. Parse ──────────────────────────────────────────────────────────────
    try:
        if filename.endswith('.csv'):
            df = None
            for enc in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(io.BytesIO(file_content), encoding=enc)
                    break
                except UnicodeDecodeError:
                    continue
            if df is None:
                raise ValueError("Could not read CSV file with any standard encoding.")
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            raise ValueError("Unsupported file type. Only CSV and Excel are supported.")
    except Exception as e:
        raise ValueError(f"Error reading file: {str(e)}")

    # ── 2. Clean ──────────────────────────────────────────────────────────────
    df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace('[^a-zA-Z0-9_]', '', regex=True)
    df = df.dropna(how='all')

    # ── 3. Profile ────────────────────────────────────────────────────────────
    profile = _generate_profile(df, filename)

    # ── 4. Upload to Supabase Storage ─────────────────────────────────────────
    session_id = str(uuid.uuid4())
    file_url = None
    try:
        sb = get_supabase()
        storage_path = f"{session_id}/{filename}"
        sb.storage.from_("datasets").upload(
            path=storage_path,
            file=file_content,
            file_options={"content-type": "application/octet-stream"}
        )
        file_url = storage_path
    except Exception as e:
        # Storage upload failure is non-fatal – app works without it
        print(f"⚠️  Supabase Storage upload failed: {e}")

    # ── 5. Save session to Supabase DB ────────────────────────────────────────
    try:
        sb = get_supabase()
        sb.table("sessions").insert({
            "session_id": session_id,
            "file_name": filename,
            "file_url": file_url,
            "column_profile": profile,
            "suggestions": []
        }).execute()
    except Exception as e:
        print(f"⚠️  Supabase DB session save failed: {e}")

    # ── 6. Store DataFrame in memory ──────────────────────────────────────────
    _memory_store[session_id] = {"df": df, "profile": profile}

    # ── 7. Preview ────────────────────────────────────────────────────────────
    preview_df = df.head(10).replace({np.nan: None})
    preview_data = preview_df.to_dict(orient='records')

    return {
        "session_id": session_id,
        "profile": profile,
        "preview": preview_data
    }


def get_session(session_id: str) -> dict | None:
    """
    Try in-memory first. If missing (server restart), reload from Supabase Storage.
    Returns {"df": DataFrame, "profile": dict} or None.
    """
    if session_id in _memory_store:
        return _memory_store[session_id]

    # ── Reload from Supabase ──────────────────────────────────────────────────
    try:
        sb = get_supabase()
        row = sb.table("sessions").select("*").eq("session_id", session_id).single().execute()
        if not row.data:
            return None
        session_row = row.data
        profile = session_row["column_profile"]
        file_url = session_row.get("file_url")
        filename = session_row.get("file_name", "")

        if not file_url:
            return None

        # Download file bytes from storage
        file_bytes = sb.storage.from_("datasets").download(file_url)

        # Re-parse
        if filename.endswith('.csv'):
            df = None
            for enc in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(io.BytesIO(file_bytes), encoding=enc)
                    break
                except UnicodeDecodeError:
                    continue
        else:
            df = pd.read_excel(io.BytesIO(file_bytes))

        if df is None:
            return None

        df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace('[^a-zA-Z0-9_]', '', regex=True)
        df = df.dropna(how='all')

        _memory_store[session_id] = {"df": df, "profile": profile}
        return _memory_store[session_id]

    except Exception as e:
        print(f"⚠️  Could not reload session {session_id} from Supabase: {e}")
        return None


def _generate_profile(df: pd.DataFrame, filename: str) -> dict:
    profile = {"filename": filename, "rows": len(df), "columns": []}

    for col in df.columns:
        col_data = df[col]
        null_count = int(col_data.isnull().sum())
        unique_count = int(col_data.nunique())

        if pd.api.types.is_numeric_dtype(col_data):
            if set(col_data.dropna().unique()) <= {0, 1}:
                col_type = 'boolean'
                stats = {
                    "min": int(col_data.min()) if not pd.isna(col_data.min()) else None,
                    "max": int(col_data.max()) if not pd.isna(col_data.max()) else None,
                }
            else:
                col_type = 'numeric'
                stats = {
                    "min": float(col_data.min()) if not pd.isna(col_data.min()) else None,
                    "max": float(col_data.max()) if not pd.isna(col_data.max()) else None,
                    "mean": float(col_data.mean()) if not pd.isna(col_data.mean()) else None,
                }
        elif pd.api.types.is_datetime64_any_dtype(col_data):
            col_type = 'datetime'
            stats = {"min": str(col_data.min()), "max": str(col_data.max())}
        else:
            try:
                if col_data.dtype == 'object' and len(col_data.dropna()) > 0:
                    first_val = str(col_data.dropna().iloc[0])
                    if any(sep in first_val for sep in ['-', '/', ':', ' ']):
                        pd.to_datetime(col_data.dropna().head(10))
                        col_type = 'datetime'
                        stats = {"sample": col_data.dropna().head(3).tolist()}
                    else:
                        raise ValueError
                else:
                    raise ValueError
            except Exception:
                col_type = 'text'
                stats = {"top_values": col_data.value_counts().head(3).index.tolist()}

        profile["columns"].append({
            "name": col,
            "type": col_type,
            "null_count": null_count,
            "unique_count": unique_count,
            **stats
        })
    return profile