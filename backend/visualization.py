import plotly.express as px
import pandas as pd
import json

def generate_chart(result, df, generated_code, question):
    """
    Analyzes the result shape and question keywords to select an appropriate Plotly chart.
    Returns the JSON representation of the chart, or None if a chart cannot be made.
    """
    question_lower = question.lower()
    
    try:
        fig = None
        
        # Case 1: Result is a Series or single-column DataFrame with an index
        # Example: df.groupby('Category')['Sales'].sum() -> Series with Category as index, Sales as values
        if isinstance(result, pd.Series):
             result = result.reset_index()
             
        if isinstance(result, pd.DataFrame):
            # Check number of columns
            cols = result.columns.tolist()
            
            if len(cols) == 2:
                col1, col2 = cols[0], cols[1]
                
                # Heuristics based on keyword
                if any(kw in question_lower for kw in ['trend', 'over time', 'monthly', 'yearly']):
                    # Sort by the first column assuming it's time
                    result = result.sort_values(by=col1)
                    fig = px.line(result, x=col1, y=col2)
                elif any(kw in question_lower for kw in ['percentage', 'proportion', 'share', 'distribution']):
                    fig = px.pie(result, names=col1, values=col2)
                elif any(kw in question_lower for kw in ['correlation', 'vs', 'versus']):
                    fig = px.scatter(result, x=col1, y=col2)
                else:
                    # Safe default: Bar chart
                    # Handle too many bars gracefully
                    if len(result) > 50:
                        result = result.head(50)
                    fig = px.bar(result, x=col1, y=col2)
            
            elif len(cols) == 1:
                # E.g. value_counts() result that became a single column dataframe, use index
                col = cols[0]
                result = result.reset_index()
                fig = px.bar(result, x=result.columns[0], y=col)
                
            # If we generated a figure, serialize it
            if fig is not None:
                # Ensure the template matches the Slate/Zinc aesthetic (dark or light depending on frontend)
                # the frontend handles dark mode, but we can set a clean default
                fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=20, b=20))
                return json.loads(fig.to_json())
                
    except Exception as e:
        print(f"Failed to generate chart: {e}")
        pass
        
    return None
