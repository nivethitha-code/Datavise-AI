"""
query_engine.py – Agentic Query Engine with:
  1. Conversational Memory  (fetches last 5 messages from Supabase)
  2. Self-Correction / Reflexion (retries on exec() failure, logs to Supabase)
  3. Smart Suggestions  (called separately via /api/generate-suggestions)
"""

import os
import pandas as pd
from groq import Groq
from dotenv import load_dotenv

import data_loader
import visualization
import insight_engine
from database import get_supabase

load_dotenv()

# ── Groq client ───────────────────────────────────────────────────────────────
_groq: Groq | None = None

def get_groq() -> Groq:
    global _groq
    if _groq is None:
        key = os.environ.get("GROQ_API_KEY")
        if not key:
            raise RuntimeError("GROQ_API_KEY is missing in your .env file.")
        _groq = Groq(api_key=key)
    return _groq

MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ── Danger list ───────────────────────────────────────────────────────────────
_BLOCKED = ['import ', 'os.', 'sys.', '__', 'eval(', 'exec(', 'open(', 'subprocess']


# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═════════════════════════════════════════════════════════════════════════════

def execute_query(session_id: str, question: str) -> dict:
    """Full pipeline: memory → code gen → safety → exec → reflexion → chart → insight → persist."""

    # 1. Get DataFrame
    session = data_loader.get_session(session_id)
    if session is None:
        raise ValueError("Session not found or expired. Please re-upload your file.")

    df: pd.DataFrame = session["df"]
    profile: dict = session["profile"]

    # 2. Fetch conversational memory
    history = _get_chat_history(session_id)

    # 3. Build prompt with memory context
    schema_str = _build_schema(df, profile)
    history_block = _format_history(history)
    prompt = _code_prompt(schema_str, history_block, question)

    # 4. Call LLM → get code
    raw_code = _llm_call(prompt, temperature=0.0, max_tokens=150)
    code_line = _extract_code(raw_code)

    # 5. Safety check
    _safety_check(code_line)

    # 6. Execute with Reflexion fallback
    result_data, final_code = _execute_with_reflexion(
        code_line, df, schema_str, question, session_id
    )

    # 7. Chart & Insight
    chart_json = visualization.generate_chart(result_data, df, final_code, question)

    if hasattr(result_data, "to_json"):
        raw_result_summary = "DataFrame/Series result"
    else:
        raw_result_summary = str(result_data)

    insight = insight_engine.generate_insight(result_data, question)

    # 8. Persist conversation to Supabase
    _save_message(session_id, "user", question)
    _save_message(session_id, "assistant", insight or raw_result_summary)

    return {
        "generated_code": final_code,
        "chart_json": chart_json,
        "insight": insight,
        "raw_result": raw_result_summary,
    }


def generate_suggestions(session_id: str) -> list[str]:
    """Ask Groq to generate 4 smart analytical questions for this dataset's columns."""
    sb = get_supabase()

    # Try to return cached suggestions first
    try:
        row = sb.table("sessions").select("suggestions, column_profile").eq("session_id", session_id).single().execute()
        if not row.data:
            raise ValueError("Session not found.")
        cached = row.data.get("suggestions", [])
        if cached:
            return cached
        profile = row.data["column_profile"]
    except Exception as e:
        raise ValueError(f"Could not load session: {e}")

    # Build column summary for the prompt
    col_lines = []
    for col in profile.get("columns", []):
        col_lines.append(f"- {col['name']} ({col['type']})")
    col_summary = "\n".join(col_lines)

    prompt = f"""A CSV dataset has these columns:
{col_summary}

Generate exactly 4 insightful analytical questions that a business owner would ask about this data.
Requirements:
- Each question must be specific to the actual column names above.
- Questions should cover: totals/aggregation, comparisons, trends, distributions.
- Return ONLY the 4 questions, one per line. No numbering, no bullets, no extra text.
"""
    raw = _llm_call(prompt, temperature=0.4, max_tokens=200)
    questions = [q.strip("•-0123456789. ").strip() for q in raw.strip().split("\n") if q.strip()][:4]

    # Cache to Supabase for future calls
    try:
        sb.table("sessions").update({"suggestions": questions}).eq("session_id", session_id).execute()
    except Exception:
        pass  # Non-fatal

    return questions


def get_history(session_id: str) -> list[dict]:
    """Public: fetch all messages for a session (for frontend load on refresh)."""
    return _get_chat_history(session_id, limit=50)


# ═════════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def _build_schema(df: pd.DataFrame, profile: dict) -> str:
    lines = ["The DataFrame called df has these columns:"]
    for col in profile.get("columns", []):
        sample_vals = df[col["name"]].dropna().unique()[:3]
        sample_str = ", ".join(map(str, sample_vals))
        lines.append(f"  - {col['name']} ({col['type']}): sample = [{sample_str}]")
    return "\n".join(lines)


def _format_history(history: list[dict]) -> str:
    if not history:
        return ""
    lines = ["Recent conversation context (use for follow-up questions):"]
    for msg in history:
        role = "User" if msg["role"] == "user" else "AI Analyst"
        lines.append(f"  {role}: {msg['content']}")
    return "\n".join(lines)


def _code_prompt(schema_str: str, history_block: str, question: str) -> str:
    history_section = f"\n{history_block}\n" if history_block else ""
    return f"""You are a Python data science assistant.
{schema_str}
{history_section}
Current question: {question}

Write exactly ONE line of Python code using Pandas that answers the current question.
Store the final answer in a variable named 'result'.
Do not include any imports, comments, or explanations.
Do not use print().
Return ONLY the raw executable code line.

Example:
result = df.groupby('Category')['Sales'].sum()
"""


def _llm_call(prompt: str, temperature: float, max_tokens: int) -> str:
    client = get_groq()
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


def _extract_code(raw: str) -> str:
    """Strip markdown fences and grab the first `result = ...` line."""
    lines = raw.strip().split("\n")
    # Strip fences
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("result"):
            return stripped
    return lines[0].strip() if lines else "result = None"


def _safety_check(code: str):
    for kw in _BLOCKED:
        if kw in code:
            raise ValueError(f"Generated code contains a blocked keyword: '{kw}'. Query rejected for safety.")


def _execute_with_reflexion(
    code_line: str,
    df: pd.DataFrame,
    schema_str: str,
    question: str,
    session_id: str,
) -> tuple:
    """
    Try exec(). If it fails:
      1. Log to Supabase agent_logs
      2. Ask Groq to fix the code (Reflexion)
      3. Try once more
    Returns (result_data, final_code_used).
    """
    local_vars = {"df": df}
    try:
        exec(code_line, {"__builtins__": {}}, local_vars)
        if "result" not in local_vars:
            raise ValueError("Code did not assign a 'result' variable.")
        return local_vars["result"], code_line

    except Exception as first_err:
        error_msg = f"{type(first_err).__name__}: {first_err}"

        # Log original failure
        _log_reflexion(session_id, code_line, error_msg, None)

        # Build correction prompt
        fix_prompt = f"""You are a Python data science assistant.
{schema_str}

Your previous code failed:
Code: {code_line}
Error: {error_msg}

Fix the code so it answers: "{question}"
Return ONLY the corrected single line of Python code (no explanation, no markdown).
"""
        try:
            fixed_raw = _llm_call(fix_prompt, temperature=0.0, max_tokens=150)
            fixed_code = _extract_code(fixed_raw)
            _safety_check(fixed_code)

            local_vars2 = {"df": df}
            exec(fixed_code, {"__builtins__": {}}, local_vars2)
            if "result" not in local_vars2:
                raise ValueError("Fixed code did not assign a 'result' variable.")

            # Log successful fix
            _log_reflexion(session_id, code_line, error_msg, fixed_code, success=True)
            return local_vars2["result"], fixed_code

        except Exception as second_err:
            raise ValueError(
                f"I couldn't compute that even after self-correction.\n"
                f"Try rephrasing your question.\n"
                f"Details: {second_err}"
            )


# ── Supabase I/O ──────────────────────────────────────────────────────────────

def _get_chat_history(session_id: str, limit: int = 5) -> list[dict]:
    try:
        sb = get_supabase()
        response = (
            sb.table("messages")
            .select("role, content, created_at")
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"⚠️  Could not fetch chat history: {e}")
        return []


def _save_message(session_id: str, role: str, content: str):
    try:
        sb = get_supabase()
        sb.table("messages").insert({
            "session_id": session_id,
            "role": role,
            "content": content[:4000],  # Truncate very long results
        }).execute()
    except Exception as e:
        print(f"⚠️  Could not save message: {e}")


def _log_reflexion(
    session_id: str,
    original_code: str,
    error_message: str,
    fixed_code: str | None,
    success: bool = False
):
    try:
        sb = get_supabase()
        sb.table("agent_logs").insert({
            "session_id": session_id,
            "original_code": original_code,
            "error_message": error_message,
            "fixed_code": fixed_code,
            "success": success,
        }).execute()
    except Exception as e:
        print(f"⚠️  Could not log reflexion: {e}")
