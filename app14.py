import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.express as px
import dash_bootstrap_components as dbc

# Sample data
df = px.data.iris()

# Image links associated with each point (in a real application, use actual image URLs)
image_links = {
    i: f"https://via.placeholder.com/150?text=Image+{i}"
    for i in range(len(df))
}

fig = px.scatter(df, x='sepal_width', y='sepal_length')
fig.update_traces(hoverinfo="none", hovertemplate=None)
# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    dcc.Store(id='value-store', data=0),  # Initialize with no data
    dcc.Graph(id="scatter-plot", figure=fig, clear_on_unhover=True),
    dcc.Tooltip(id="graph-tooltip"),
    html.Div(id='image-container',
             style={'display': 'flex', 'flexWrap': 'wrap', 'margin-top': '20px'}),
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Image Details")),
            dbc.ModalBody(html.Img(id='modal-image', style={'width': '100%'})),
            dbc.ModalFooter(
                dbc.Button("Close", id='close-modal',
                           className='ms-auto', n_clicks=0)
            ),
        ],
        id='image-modal',
        is_open=False,
    )
])


@app.callback(
    [Output("graph-tooltip", "show"),
     Output("graph-tooltip", "bbox"),
     Output("graph-tooltip", "children")],
    [Input("scatter-plot", "hoverData")]
)
def display_hover(hoverData):
    if hoverData is None:
        return False, dash.no_update, dash.no_update

    pt = hoverData["points"][0]
    bbox = pt.get("bbox", None)
    num = pt["pointIndex"]

    img_src = image_links[num]

    children = [
        html.Div([
            html.Img(src=img_src, style={"width": "100%"}),
        ], style={'width': '200px', 'white-space': 'normal'})
    ]

    return True, bbox, children


@app.callback(
    Output('image-container', 'children'),
    Input('scatter-plot', 'clickData'),
    Input({'type': 'delete-btn', 'index': dash.dependencies.ALL}, 'n_clicks'),
    State('image-container', 'children')
)
def display_images(clickData, n_clicks_list, children):
    ctx = dash.callback_context
    if not ctx.triggered:
        return children
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if triggered_id == 'scatter-plot':
        if clickData:
            if children is None:
                children = []
            point_index = clickData['points'][0]['pointIndex']
            new_image = html.Div([
                html.Button('×', id={'type': 'delete-btn', 'index': point_index}, n_clicks=0, style={'background-color': 'red',
                            'color': 'white', 'border': 'none', 'cursor': 'pointer', 'position': 'absolute', 'top': '5px', 'right': '5px'}),
                html.Img(
                    src=image_links[point_index],
                    style={'width': '150px', 'height': '150px',
                        'margin': '5px', 'cursor': 'pointer'},
                    id={'type': 'dynamic-img', 'index': point_index}
                )
            ], style={'position': 'relative'}, id={'type': 'dynamic-div-img', 'index': point_index})
            return children + [new_image]
        return children
    else:
        children = [c for c in children if c['props']['id']['index'] != eval(triggered_id)['index']]
    return children


@app.callback(
    Output('image-modal', 'is_open'),
    Output('modal-image', 'src'),
    Output('value-store', 'data'),
    Input({'type': 'dynamic-img', 'index': dash.dependencies.ALL}, 'n_clicks'),
    Input('close-modal', 'n_clicks'),
    State('value-store', 'data'),
    State('image-container', 'children'),
    State('image-modal', 'is_open'),
    State({'type': 'dynamic-img', 'index': dash.dependencies.ALL}, 'n_clicks_timestamp')
)
def toggle_modal(img_n_clicks, close_n_clicks, data, children, is_open, timestamps):
    ctx = dash.callback_context

    if not ctx.triggered:
        return is_open, None, data

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if 'dynamic-img' in triggered_id:
        valid_timestamps = [timestamp for timestamp in timestamps if timestamp is not None]
        if valid_timestamps:
            latest_click = max(valid_timestamps)
            latest_index = timestamps.index(latest_click)
            image_index = children[latest_index]['props']['id']['index']
            if eval(triggered_id)['index'] == image_index and latest_click > data:
                data = latest_click
                return not is_open, image_links[image_index], data
    elif 'close-modal' in triggered_id:
        return not is_open, None, data

    return is_open, None, data


if __name__ == '__main__':
    app.run_server(debug=True)
