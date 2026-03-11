import sys
import os

# Mock data_loader and visualization if needed, but they should be there
import query_engine
import data_loader
import pandas as pd

# Create a mock session
df = pd.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]})
session_id = "test_session"

# Directly inject into memory cache
data_loader._memory_store[session_id] = {
    "df": df, 
    "profile": {
        "columns": [
            {"name": "A", "type": "numeric"},
            {"name": "B", "type": "categorical"}
        ]
    }
}

print("Starting test query...")
try:
    for chunk in query_engine.execute_query_stream(session_id, "Show total of A"):
        print(f"Chunk: {chunk}")
except Exception as e:
    print(f"FAILED: {e}")