import plotly.express as px
import pandas as pd
import json

import plotly.io as pio

def generate_chart_fig(result, df, question):
    """Internal helper to return the raw plotly figure object."""
    question_lower = question.lower()
    try:
        fig = None
        if isinstance(result, pd.Series):
             result = result.reset_index()
             
        if isinstance(result, pd.DataFrame):
            cols = result.columns.tolist()
            if len(cols) == 2:
                col1, col2 = cols[0], cols[1]
                if any(kw in question_lower for kw in ['trend', 'over time', 'monthly', 'yearly']):
                    result = result.sort_values(by=col1)
                    fig = px.line(result, x=col1, y=col2)
                elif any(kw in question_lower for kw in ['percentage', 'proportion', 'share', 'distribution']):
                    fig = px.pie(result, names=col1, values=col2)
                elif any(kw in question_lower for kw in ['correlation', 'vs', 'versus']):
                    fig = px.scatter(result, x=col1, y=col2)
                else:
                    if len(result) > 50: result = result.head(50)
                    fig = px.bar(result, x=col1, y=col2)
            elif len(cols) == 1:
                col = cols[0]
                result = result.reset_index()
                fig = px.bar(result, x=result.columns[0], y=col)
            
            if fig is not None:
                fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=20, b=20))
                return fig
    except Exception as e:
        print(f"Failed to generate fig: {e}")
    return None

def generate_chart(result, df, generated_code, question):
    fig = generate_chart_fig(result, df, question)
    return json.loads(fig.to_json()) if fig else None

def export_chart_as_image(result, df, question) -> bytes | None:
    """Exports a chart as a PNG byte buffer using kaleido."""
    fig = generate_chart_fig(result, df, question)
    if fig:
        try:
            return pio.to_image(fig, format="png")
        except Exception as e:
            print(f"Kaleido export failed: {e}")
    return None