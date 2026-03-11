import pandas as pd
import query_engine

def run_automated_analysis(session_id: str) -> list[dict]:
    """
    Runs 3 standard analyses on a dataset immediately after upload.
    Returns a list of result dictionaries.
    """
    analyses = [
        "Return a dataset containing the category counts for the most prominent categorical column.",
        "Return a dataset containing the top 10 highest values for the primary numeric column.",
        "Return a dataset aggregated by date for a trend line if a time column exists, otherwise the 10 lowest values for the primary numeric column."
    ]
    
    results = []
    for q in analyses:
        try:
            # We use the synchronous execute_query to get final results directly
            # This will also populate the chat history automatically
            res = query_engine.execute_query(session_id, q)
            results.append({
                "question": q,
                "insight": res.get("insight"),
                "chart_json": res.get("chart_json"),
                "raw_result": res.get("raw_result"),
                "generated_code": res.get("generated_code")
            })
        except Exception as e:
            print(f"Automated analysis failed for '{q}': {e}")
            results.append({
                "question": q,
                "insight": None,
                "chart_json": None,
                "raw_result": f"Analysis Generation Failed:\n{e}"
            })
            
    return results