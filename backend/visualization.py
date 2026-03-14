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
            if len(cols) >= 2:
                col1, col2 = cols[0], cols[1]
                # 📈 Trend / Area
                if any(kw in question_lower for kw in ['trend', 'over time', 'monthly', 'yearly', 'progress']):
                    result = result.sort_values(by=col1)
                    if 'area' in question_lower:
                        fig = px.area(result, x=col1, y=col2)
                    else:
                        fig = px.line(result, x=col1, y=col2)
                # 🍕 Pie
                elif any(kw in question_lower for kw in ['percentage', 'proportion', 'share', 'distribution', 'pie']):
                    fig = px.pie(result, names=col1, values=col2)
                # 📍 Scatter / Correlation
                elif any(kw in question_lower for kw in ['correlation', 'vs', 'versus', 'scatter', 'relationship']):
                    fig = px.scatter(result, x=col1, y=col2)
                # 📦 Box / Violin Plot
                elif any(kw in question_lower for kw in ['box', 'outlier', 'spread', 'variance', 'range', 'violin', 'variation']):
                    if 'violin' in question_lower:
                        fig = px.violin(result, x=col1, y=col2, box=True)
                    else:
                        fig = px.box(result, x=col1, y=col2)
                # ☀️ Sunburst / Hierarchy
                elif any(kw in question_lower for kw in ['sunburst', 'hierarchy', 'nested']):
                    fig = px.sunburst(result, path=[col1, col2])
                # 🌡️ Heatmap / Matrix
                elif any(kw in question_lower for kw in ['heatmap', 'matrix', 'density']):
                    fig = px.density_heatmap(result, x=col1, y=col2)
                # 🫧 Bubble / Size
                elif any(kw in question_lower for kw in ['bubble', 'size']) and len(cols) >= 3:
                    fig = px.scatter(result, x=cols[0], y=cols[1], size=cols[2])
                # 📊 Bar (Default)
                else:
                    if len(result) > 50: result = result.head(50)
                    fig = px.bar(result, x=col1, y=col2)
            elif len(cols) == 1:
                col = cols[0]
                # 📉 Histogram / Frequency
                if any(kw in question_lower for kw in ['histogram', 'frequency', 'count', 'distribution']):
                    fig = px.histogram(result, x=col)
                else:
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