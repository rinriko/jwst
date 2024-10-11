import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

app = dash.Dash(__name__)

# Sample data for the plot
fig = go.Figure(
    data=go.Scatter(
        x=[1, 2, 3, 4],
        y=[10, 11, 12, 13],
        mode="markers",
        marker=dict(size=10)
    )
)

# Define annotations with clickable properties
annotations = [
    dict(
        x=1,
        y=10,
        xref="x",
        yref="y",
        text="Annotation 1",
        showarrow=True,
        arrowhead=2,
        ax=0,
        ay=-40,
        font=dict(color='blue'),
        arrowcolor='blue',
        clicktoshow='onoff',  # Set to 'onoff' to toggle visibility on click
    ),
    dict(
        x=2,
        y=11,
        xref="x",
        yref="y",
        text="Annotation 2",
        showarrow=True,
        arrowhead=2,
        ax=0,
        ay=-40,
        font=dict(color='blue'),
        arrowcolor='blue',
        clicktoshow='onoff',  # Set to 'onoff' to toggle visibility on click
    )
]

# Update the layout to include annotations
fig.update_layout(
    annotations=annotations
)

@app.callback(
    Output("output-div", "children"),
    Input("your-figure-id", "clickAnnotationData")  # Use clickAnnotationData
)
def handle_annotation_click(click_annotation_data):
    if click_annotation_data:
        # Access information about the clicked annotation
        annotation_text = click_annotation_data['annotation']['text']
        return f"You clicked on: {annotation_text}"

    return "Click on an annotation to see details"

app.layout = html.Div([
    dcc.Graph(id="your-figure-id", figure=fig),
    html.Div(id="output-div")
])

if __name__ == "__main__":
    app.run_server(debug=True)
