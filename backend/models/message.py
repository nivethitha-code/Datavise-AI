MESSAGES_SQL = """
CREATE TABLE IF NOT EXISTS messages (
    id          BIGSERIAL PRIMARY KEY,
    session_id  UUID REFERENCES sessions(session_id) ON DELETE CASCADE,
    role        TEXT CHECK (role IN ('user', 'assistant')) NOT NULL,
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
"""