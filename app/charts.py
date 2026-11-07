import plotly.graph_objects as go


def build_chart(columns: list, rows: list):
    """Pick a sensible chart for the result. Returns Plotly JSON or None."""
    # A chart needs at least 2 columns and 2 rows
    if len(columns) < 2 or len(rows) < 2:
        return None

    labels = [str(r[0]) for r in rows]
    values = [r[1] for r in rows]

    # The second column must be numeric
    if not all(isinstance(v, (int, float)) for v in values):
        return None

    fig = go.Figure(go.Bar(x=labels, y=values))
    fig.update_layout(
        title=f"{columns[1]} by {columns[0]}",
        xaxis_title=columns[0],
        yaxis_title=columns[1],
    )
    return fig.to_json()