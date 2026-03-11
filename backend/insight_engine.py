from groq import Groq
import pandas as pd

import os
from dotenv import load_dotenv
load_dotenv()

# Lazy initialization
def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        return None
    return Groq(api_key=api_key)

client = None

def generate_insight(result, question: str) -> str:
    """
    Takes the raw result data and sends it to the LLM to get a plain-English explanation.
    """
    global client

    # Convert result to string representation
    if isinstance(result, (pd.DataFrame, pd.Series)):
        try:
            # to_markdown() requires 'tabulate' package
            if len(result) > 20:
                data_str = result.head(20).to_markdown() + "\n... (data truncated)"
            else:
                data_str = result.to_markdown()
        except ImportError:
            # Fallback if tabulate is not installed
            if len(result) > 20:
                data_str = result.head(20).to_string() + "\n... (data truncated)"
            else:
                data_str = result.to_string()
    else:
        data_str = str(result)
        
    prompt = f"""You are a professional Data Analyst.
A user asked this question about their data: "{question}"
And here is the resulting data calculated by python:
{data_str}

Please write a 2-3 sentence summary explaining what this result means in plain English, using the actual numbers.
Be direct, clear, and professional. 
Do not mention the code, python, or how it was calculated.
Speak directly about the insights.
"""

    if client is None:
        client = get_groq_client()
        if client is None:
             return "Insight generation requires GROQ_API_KEY. Result data: " + str(result)[:100]

    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            temperature=0.3,
            max_tokens=150,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Insight generation failed. Result data: {data_str[:100]}..."
