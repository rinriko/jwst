import dash
from dash import dcc, html
from dash.dependencies import Input, Output

app = dash.Dash(__name__)

# Sample data for images
images = [
    {'src': 'https://via.placeholder.com/150?text={"image1"}', 'index': 0, 'annotation': 'Image 1'},
    {'src': 'https://via.placeholder.com/150?text={"image2"}', 'index': 1, 'annotation': 'Image 2'},
    {'src': 'https://via.placeholder.com/150?text={"image3"}', 'index': 2, 'annotation': 'Image 3'},
    # Add more images as needed...
]


# Function to create the image divs dynamically
def create_image_divs():
    return [
        html.Div(
            style={'position': 'relative', 'margin': '10px'},
            children=[
                html.Img(
                    src=img['src'],
                    id={'type': 'dynamic-img', 'index': img['index']},
                    style={'width': '150px', 'height': '150px', 'cursor': 'pointer'},
                    title=img['annotation'],
                    className='image'
                ),
                html.Button('×', id={'type': 'delete-btn', 'index': img['index']}, n_clicks=0, style={
                    'background-color': 'red',
                    'color': 'white',
                    'border': 'none',
                    'cursor': 'pointer',
                    'position': 'absolute',
                    'top': '5px',
                    'right': '5px'
                }),
                html.Div(
                    img['annotation'],
                    style={
                        'position': 'absolute',
                        'top': '5px',
                        'left': '5px',
                        'background-color': 'rgba(0, 0, 0, 0.5)',
                        'color': 'white',
                        'padding': '2px 5px',
                        'border-radius': '3px',
                        'font-size': '12px',
                        'font-weight': 'bold'
                    }
                )
            ]
        ) for img in images
    ]

# App layout
app.layout = html.Div([
    html.Div(id='image-container', style={'display': 'flex', 'flex-wrap': 'wrap'}, children=create_image_divs()),
    dcc.Store(id='hovered-image')  # Store to manage hovered image state
])

# Callback to manage hover state
@app.callback(
    Output('hovered-image', 'data'),
    [Input({'type': 'dynamic-img', 'index': dash.dependencies.ALL}, 'n_hovered')]
)
def on_image_hover(n_hovered):
    hovered_index = [i for i, count in enumerate(n_hovered) if count is not None and count > 0]
    return {'index': hovered_index[0]} if hovered_index else {'index': None}

# Callback to dynamically change the style of hovered image
@app.callback(
    Output({'type': 'dynamic-img', 'index': dash.dependencies.ALL}, 'style'),
    Input('hovered-image', 'data')
)
def update_hovered_style(hovered_image):
    styles = [{'border': 'none'}] * len(images)  # Reset styles
    if hovered_image['index'] is not None:
        index = hovered_image['index']
        styles[index] = {'border': '2px solid blue'}  # Change border for hovered image
    return styles


if __name__ == '__main__':
    app.run_server(debug=True, port=8051)
