AGENT_LOGS_SQL = """
CREATE TABLE IF NOT EXISTS agent_logs (
    id              BIGSERIAL PRIMARY KEY,
    session_id      UUID REFERENCES sessions(session_id) ON DELETE CASCADE,
    original_code   TEXT,
    error_message   TEXT,
    fixed_code      TEXT,
    success         BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
"""
