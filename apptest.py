import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd

app = dash.Dash(__name__)

# Sample data
df = pd.DataFrame({
    'x': [1, 2, 3],
    'y': [4, 1, 2],
    'color': ['blue', 'blue', 'blue']
})

app.layout = html.Div([
    dcc.Graph(id='graph', figure=go.Figure(
        data=[go.Scatter(x=df['x'], y=df['y'], mode='markers', marker=dict(color=df['color']))],
        layout=go.Layout(clickmode='event+select')
    )),
    html.Div(id='output-container')
])

@app.callback(
    Output('graph', 'figure'),
    Input('graph', 'clickData'),
    State('graph', 'figure')
)
def update_color(clickData, figure):
    if clickData:
        # Get the index of the clicked point
        point_index = clickData['points'][0]['pointIndex']

        # Update the color of the clicked point
        figure['data'][0]['marker']['color'][point_index] = 'red'

    return figure

if __name__ == '__main__':
    app.run_server(debug=True)