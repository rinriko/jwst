import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

app = dash.Dash(__name__)

# Sample figure for demonstration
sample_figure = {
    "data": [go.Scatter(x=[1, 2, 3], y=[3, 1, 6], mode="markers")],
    "layout": go.Layout(title="Right-click on this plot")
}

# Dash layout
app.layout = html.Div([
    dcc.Graph(id="example-graph", figure=sample_figure),
    html.Div(id="custom-menu", style={"display": "none", "position": "absolute", "background": "#f9f9f9", 
                                      "border": "1px solid #ccc", "zIndex": 1000})
])

# Callback to show custom menu on right-click
@app.callback(
    Output("custom-menu", "style"),
    Input("example-graph", "relayoutData"),
    [Input("example-graph", "n_clicks_timestamp")]
)
def show_custom_menu(relayoutData, click_timestamp):
    # Update the style of the custom menu to make it appear at the mouse position
    if click_timestamp is not None:
        return {"display": "block", "left": f"{relayoutData['x']}px", 
                "top": f"{relayoutData['y']}px"}
    return {"display": "none"}

if __name__ == "__main__":
    app.run_server(debug=True, port=8051)
