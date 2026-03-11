from .session import SESSIONS_SQL
from .message import MESSAGES_SQL
from .agent_log import AGENT_LOGS_SQL

TABLES_SQL = SESSIONS_SQL + MESSAGES_SQL + AGENT_LOGS_SQL
