import os
from dotenv import load_dotenv
load_dotenv()
import pandas as pd
import json
import re
from groq import Groq
from database import get_supabase
import visualization
import data_loader

MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
_BLOCKED = ["import", "os", "sys", "eval", "open", "subprocess", "shutil", "__builtins__"]

def get_groq():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY missing from environment.")
    return Groq(api_key=api_key)

def get_history(session_id: str) -> list[dict]:
    """Public function to retrieve chat history."""
    return _get_chat_history(session_id)

def generate_suggestions(session_id: str) -> list[str]:
    """
    Analyzes the data schema and history to suggest 3 intelligent follow-up questions.
    """
    session = data_loader.get_session(session_id)
    if not session:
        raise ValueError("Session not found.")
    
    df = session["df"]
    profile = session["profile"]
    schema_str = _build_schema(df, profile)
    history = _get_chat_history(session_id)
    history_block = _format_history(history)

    prompt = f"""You are a smart Data Analyst. Based on this data schema and history, suggest 3 concise, analytical questions the user should ask next.
{schema_str}
{history_block}
Return ONLY a JSON list of strings. No descriptions.
Example: ["Show sales by region", "What is the trend over time?"]
"""
    try:
        raw = _llm_call(prompt, temperature=0.7, max_tokens=150)
        # Attempt to find JSON in the response
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
             return json.loads(match.group())
        return json.loads(raw)
    except:
        return ["Show total rows", "Describe each column", "What are the top 5 values?"]

# ═════════════════════════════════════════════════════════════════════════════
# MULTI-AGENT PERSONAS
# ═════════════════════════════════════════════════════════════════════════════

def _data_agent_prompt(schema_str: str, history_block: str, question: str) -> str:
    return f"""You are the **Data Analyst Agent**. Your ONLY job is to write Python/Pandas code that performs PROPER, deep analysis to answer data questions accurately.
{schema_str}
{history_block}
Current question: {question}

Write ONE line of Python code (using Pandas only) that computes the answer and stores it in 'result'.
The variable 'result' MUST be a pandas DataFrame, pandas Series, or a scalar value.

STRICT RULES:
- NEVER use matplotlib, plt, seaborn, plotly or any charting library. A separate charting engine handles visualization.
- NEVER call .plot(), .show(), .draw(), or any rendering method.
- NEVER write import statements.
- NEVER write markdown, comments, or explanations — ONLY the raw Python code line.
- Use only column names from the schema above.
- If the user says 'pie chart', 'bar chart', 'line chart', 'box plot', 'histogram', or 'area chart' etc., still only return the underlying DATA, not a chart.

Good examples:
  result = df['emotion'].value_counts().reset_index()
  result = df.groupby('emotion')['mfcc_0'].mean().reset_index()
  result = df['mfcc_0'].max()
  result = df['age'].dropna() # For histogram/box plot

Bad examples (NEVER do this):
  df.plot(kind='pie')  ← FORBIDDEN
  plt.bar(...)         ← FORBIDDEN
  import matplotlib    ← FORBIDDEN
"""

def _viz_agent_prompt(question: str, data_summary: str) -> str:
    return f"""You are the **Visualization Expert Agent**. Your goal is to suggest the best way to visualize the result.
Question: {question}
Data Summary: {data_summary}

Based on the data, what is the single most effective chart type? (e.g., Pie, Bar, Line, Scatter, None)
Return ONLY the chart type name.
"""

def _insight_agent_prompt(question: str, result_summary: str) -> str:
    return f"""You are the **Insight Consultant Agent**. Your goal is to explain the data in a professional, business-friendly way.
Question: {question}
Result: {result_summary}

Provide a concise, 2-3 sentence summary of what this data means. 
Focus on the "why" or the business impact. Do not just repeat the numbers. 
"""

# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC API (GENERATOR FOR STREAMING)
# ═════════════════════════════════════════════════════════════════════════════

def execute_query_stream(session_id: str, question: str, save_history: bool = True):
    """
    Multi-Agent pipeline that yields status logs in real-time.
    Routes conversational questions to a direct LLM, data questions to the full pipeline.
    Yields dicts with 'status' or 'final_result'.
    """
    try:
        print(f"🚀 [Query] Starting stream for session: {session_id}")
        # 1. Setup & Context
        yield {"status": "🔍 Identifying data schema and context..."}
        session = data_loader.get_session(session_id)
        if session is None:
            yield {"error": "Session not found."}
            return

        df: pd.DataFrame = session["df"]
        profile: dict = session["profile"]
        history = _get_chat_history(session_id)
        schema_str = _build_schema(df, profile)
        history_block = _format_history(history)

        # 1b. Intent Classification: is this a data question or a conversational question?
        intent_prompt = f"""You are a question classifier.
Classify the following question as either "data" or "chat".
- "data": questions that require querying, aggregating, or visualizing the dataset (e.g., "how many rows?", "show me a chart", "what is the average of X?", "correlation between X and Y")
- "chat": general conversation, explanations, greetings, methodology questions, or anything that doesn't require running code on the data (e.g., "what does MFCC mean?", "hi", "explain this", "what should I analyze?", "thank you")

Question: {question}
Reply with ONLY one word: "data" or "chat"."""

        intent = _llm_call(intent_prompt, temperature=0.0, max_tokens=5).strip().lower()
        print(f"🧭 [Query] Intent classified as: '{intent}'")

        if "chat" in intent:
            # Fast-path: answer conversationally using the dataset context
            yield {"status": "💬 Thinking about your question..."}
            chat_prompt = f"""You are 'Datavise AI', a friendly and expert Data Analyst.
The user has uploaded a dataset. Context for your awareness:
{schema_str}

User's message: "{question}"

Instructions:
1. If the user is just saying 'hi', 'hello', or greeting you, respond warmly and offer to help analyze their data.
2. If the user asks a general question, answer in a professional yet conversational way.
3. Be concise. Avoid dumping technical schema details unless specifically asked.
4. Do NOT generate any Python code. Answer in plain English."""
            answer = _llm_call(chat_prompt, temperature=0.7, max_tokens=400)

            if save_history:
                _save_message_async(session_id, "user", question)
                _save_message_async(session_id, "assistant", answer)

            yield {
                "final_result": {
                    "generated_code": None,
                    "chart_json": None,
                    "insight": answer,
                    "raw_result": None,
                    "agents_involved": ["Chat Agent"]
                }
            }
            return

        # 2. Data Agent: Generate Code
        print("🤖 [Query] Step 2: Generating code...")
        yield {"status": "🤖 Data Agent: Generating analytical solution..."}
        prompt = _data_agent_prompt(schema_str, history_block, question)
        raw_code = _llm_call(prompt, temperature=0.0, max_tokens=300)
        code_line = _extract_code(raw_code)
        _safety_check(code_line)

        # 3. Execution & Reflexion
        print("⚙️ [Query] Step 3: Executing code...")
        yield {"status": "⚙️  Executing calculation and verifying accuracy..."}
        result_data, final_code = _execute_with_reflexion_stream(
            code_line, df, schema_str, question, session_id
        )

        # 4. Viz Agent: Chart Selection
        print("📊 [Query] Step 4: Visualizing...")
        yield {"status": "📊 Visualization Agent: Designing optimal chart type..."}
        data_summary = str(result_data)[:200]
        viz_prompt = _viz_agent_prompt(question, data_summary)
        suggested_viz = _llm_call(viz_prompt, temperature=0.0, max_tokens=20).strip()
        
        chart_json = visualization.generate_chart(result_data, df, final_code, question)

        # 5. Insight Agent: Storytelling
        print("💡 [Query] Step 5: Generating insights...")
        yield {"status": "💡 Insight Agent: Formulating business takeaway..."}
        insight_prompt = _insight_agent_prompt(question, data_summary)
        insight = _llm_call(insight_prompt, temperature=0.4, max_tokens=250)

        # 6. Persistence
        if save_history:
            _save_message_async(session_id, "user", question)
            _save_message_async(session_id, "assistant", insight)

        print("✅ [Query] Step 6: Complete!")
        yield {
            "final_result": {
                "generated_code": final_code,
                "chart_json": chart_json,
                "insight": insight,
                "raw_result": str(result_data)[:500],
                "agents_involved": ["Data Analyst", "Viz Expert", "Insight Consultant"]
            }
        }

    except Exception as e:
        yield {"error": str(e)}



def execute_query(session_id: str, question: str, save_history: bool = False) -> dict:
    """Legacy wrapper for synchronous calls. Defaults save_history to False for internal tasks."""
    res = {}
    for chunk in execute_query_stream(session_id, question, save_history=save_history):
        if "final_result" in chunk:
            res = chunk["final_result"]
        elif "error" in chunk:
            raise Exception(chunk["error"])
    return res


# ═════════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS (UPDATED)
# ═════════════════════════════════════════════════════════════════════════════

def _execute_with_reflexion_stream(
    code_line: str,
    df: pd.DataFrame,
    schema_str: str,
    question: str,
    session_id: str,
) -> tuple:
    local_vars = {"df": df}
    try:
        exec(code_line, {"__builtins__": {}}, local_vars)
        if "result" not in local_vars:
            raise ValueError("Code did not assign a 'result' variable.")
        return local_vars["result"], code_line

    except Exception as first_err:
        error_msg = f"{type(first_err).__name__}: {first_err}"
        _log_reflexion(session_id, code_line, error_msg, None)

        # Correction
        fix_prompt = f"""You are a Python data science assistant.
Previous code: {code_line} failed with error: {error_msg}
Fix it so it answers: "{question}"
Target columns: {schema_str}
Return ONLY the corrected single line of Python code.
"""
        fixed_raw = _llm_call(fix_prompt, temperature=0.0, max_tokens=150)
        fixed_code = _extract_code(fixed_raw)
        _safety_check(fixed_code)

        local_vars2 = {"df": df}
        exec(fixed_code, {"__builtins__": {}}, local_vars2)
        if "result" not in local_vars2:
            raise ValueError("Fixed code did not assign a 'result' variable.")

        _log_reflexion(session_id, code_line, error_msg, fixed_code, success=True)
        return local_vars2["result"], fixed_code

# Standard helpers remain mostly the same but ensure clean interfaces

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
    lines = ["Recent conversation context:"]
    for msg in history:
        role = "User" if msg["role"] == "user" else "AI"
        lines.append(f"  {role}: {msg['content']}")
    return "\n".join(lines)


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
    lines = raw.strip().split("\n")
    if lines and lines[0].startswith("```"): lines = lines[1:]
    if lines and lines[-1].startswith("```"): lines = lines[:-1]
    for line in lines:
        if line.strip().startswith("result"): return line.strip()
    return lines[0].strip() if lines else "result = None"


def _safety_check(code: str):
    for kw in _BLOCKED:
        if kw in code:
            raise ValueError(f"Security: Blocked keyword '{kw}'")


def _get_chat_history(session_id: str, limit: int = 5) -> list[dict]:
    try:
        sb = get_supabase()
        response = (
            sb.table("messages")
            .select("role, content, created_at")
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .limit(50) # Increased for PDF reports
            .execute()
        )
        return response.data or []
    except Exception:
        return []


def _save_message_async(session_id: str, role: str, content: str):
    # Standard save (simple Supabase insert)
    try:
        sb = get_supabase()
        sb.table("messages").insert({
            "session_id": session_id,
            "role": role,
            "content": content[:4000],
        }).execute()
    except Exception as e:
        print(f"❌ Failed to save message to Supabase: {e}")

def _log_reflexion(session_id, orig, err, fixed, success=False):
    try:
        sb = get_supabase()
        sb.table("agent_logs").insert({
            "session_id": session_id,
            "original_code": orig,
            "error_message": err,
            "fixed_code": fixed,
            "success": success,
        }).execute()
    except Exception as e:
        print(f"❌ Failed to log reflexion to Supabase: {e}")