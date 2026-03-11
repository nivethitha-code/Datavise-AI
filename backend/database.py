"""
Centralized Database & Supabase Module.
Handles:
1. Supabase Client Initialization
2. Python 3.14+ httpx Monkey-patching
3. Automated Database Table Creation
"""

import os
import psycopg2
from urllib.parse import urlparse, quote, urlunparse
from dotenv import load_dotenv

# ── Monkey-patch httpx for Supabase compatibility on newer/experimental Python envs ──
import httpx

def _patch_httpx_init(client_class):
    original_init = client_class.__init__
    def patched_init(self, *args, **kwargs):
        # httpx 0.28.0+ renamed/removed 'proxy' argument in favor of 'proxies'
        if "proxy" in kwargs and "proxies" not in kwargs:
            kwargs["proxies"] = kwargs.pop("proxy")
        return original_init(self, *args, **kwargs)
    client_class.__init__ = patched_init

_patch_httpx_init(httpx.Client)
_patch_httpx_init(httpx.AsyncClient)
# ──────────────────────────────────────────────────────────────────────────────────

from supabase import create_client, Client
from models import TABLES_SQL

load_dotenv()

_supabase: Client | None = None

def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in your .env file.")
        _supabase = create_client(url, key)
    return _supabase

def init_db():
    """
    Automated table creation on startup via psycopg2.
    Uses DATABASE_URL from .env.
    """
    raw_url = os.environ.get("DATABASE_URL")
    if not raw_url:
        print("⚠️  DATABASE_URL missing, skipping automated DB initialization.")
        return

    try:
        # Avoid urlparse entirely to stay compatible with experimental Python versions (3.14)
        # URL format: postgresql://user:pass@host:port/dbname
        prefix = "postgresql://"
        if not raw_url.startswith(prefix):
            raise ValueError("DATABASE_URL must start with postgresql://")
            
        inner = raw_url[len(prefix):] # user:pass@host:port/dbname
        user_info, host_info = inner.rsplit("@", 1)
        user, password = (user_info.split(":", 1) if ":" in user_info else (user_info, ""))
        
        # Clean brackets if present
        if password.startswith("[") and password.endswith("]"):
            password = password[1:-1]
        
        host_port, dbname = (host_info.split("/", 1) if "/" in host_info else (host_info, "postgres"))
        host, port = (host_port.split(":", 1) if ":" in host_port else (host_port, "5432"))

        print(f"🔄 [DB] Initializing database tables on {host}...")
        # Use keyword arguments to bypass any internal urlparse/ipaddress validation bugs
        conn = psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=dbname,
            connect_timeout=10
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Ensure the schema exists and explicitly target it
        cur.execute("CREATE SCHEMA IF NOT EXISTS ai_analyst;")
        cur.execute("SET search_path TO ai_analyst;")
        cur.execute(TABLES_SQL)
        cur.close()
        conn.close()
        print("✅ [DB] Database initialization complete (table schema: ai_analyst).")
    except Exception as e:
        print(f"❌ [DB] Error during database initialization: {e}")

# Create Supabase Storage bucket
def init_storage():
    try:
        sb = get_supabase()
        try:
            sb.storage.create_bucket("datasets", options={"public": False})
            print("✅ [Storage] Bucket 'datasets' initialized.")
        except Exception as bucket_err:
            if "already exists" in str(bucket_err).lower():
                pass # Silently proceed
            else:
                print(f"⚠️  [Storage] Bucket note: {bucket_err}")
    except Exception as e:
        print(f"⚠️  [Storage] Initialization failed: {e}")
