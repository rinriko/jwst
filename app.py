import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, callback_context
from dash.dependencies import Input, Output, State
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.figure_factory as ff
from pathlib import Path
import re
import copy
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from astropy.time import Time
from astropy import units as u, constants as c
from collections import defaultdict
import config
from dash_iconify import DashIconify

from components import data_type_options, get_epoch, xAxis_options, color_list, sidebar, navbar, content, update_trace, update_df, modal

dash_app = dash.Dash(__name__, external_stylesheets=[
                     dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME])
server = dash_app.server

dash_app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dcc.Location(id='url', refresh=False),
                navbar,
                modal
            ]
        ),
        dbc.Row(
            [
                dbc.Col(sidebar, width=2, className='bg-light'),
                dbc.Col(content, width=10),
            ]
        ),
    ],
    fluid=True,
)

# sidebar

@dash_app.callback(
    Output("download-data", "data"),
    Input("btn-download", "n_clicks"),
    State('plot-chart', 'figure'),
    prevent_initial_call=True
)
def download_data(n_clicks, fig):
    import pandas as pd
    from io import StringIO

    # Initialize a dictionary to hold phase values and trace data
    data_dict = {}
    phase_values = None  # To store the common x values

    # Loop through each trace in the figure to extract data
    for trace in fig['data']:
        if 'x' in trace and 'y' in trace:
            if phase_values is None:
                phase_values = trace['x']  # Set the common phase values
                # Format phase values to 2 decimal places
                phase_values = [round(phase, 2) for phase in phase_values]
                data_dict['Phase'] = phase_values  # Initialize Phase column
            
            # Store the trace values using trace name as column
            data_dict[trace['name']] = trace['y']
    
    # Create DataFrame from the dictionary
    combined_df = pd.DataFrame(data_dict)
    
    # Convert DataFrame to CSV
    csv_string = combined_df.to_csv(index=False)
    
    # Return the CSV as a downloadable response
    return dict(content=csv_string, filename="plot_data.csv")



@dash_app.callback(
    Output('noOfBins', 'value'),
    Output('noOfBinsValue', 'value'),
    Output('noOfDataPoint', 'value'),
    Output('noOfDataPointValue', 'value'),
    Input('noOfBins', 'value'),
    Input('noOfBinsValue', 'value'),
    Input('noOfDataPoint', 'value'),
    Input('noOfDataPointValue', 'value')
)
def sync_input_slider(noOfBins, noOfBinsValue, noOfDataPoint, noOfDataPointValue):
    ctx = dash.callback_context
    if not ctx.triggered:
        return noOfBins, noOfBins, noOfDataPoint, noOfDataPoint
    else:
        input_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if input_id == 'noOfBins':
            return noOfBins, noOfBins, noOfDataPoint, noOfDataPoint
        elif input_id == 'noOfBinsValue':
            return noOfBinsValue, noOfBinsValue, noOfDataPoint, noOfDataPoint
        elif input_id == 'noOfDataPoint':
            return noOfBins, noOfBins, noOfDataPoint, noOfDataPoint
        elif input_id == 'noOfDataPointValue':
            return noOfBins, noOfBins, noOfDataPointValue, noOfDataPointValue


@dash_app.callback(
    Output('avgGroup', 'style'),
    Output('avgGroup1', 'style'),
    Output('avgGroup2', 'style'),
    Input('dataType', 'value'),
    Input('xAxis', 'value'),
)
def toggle_avg_sections(data_type, xAxis):
    avg_group_style = {'display': 'none'} if data_type != 'average' else {}
    avg_group1_style = {
        'display': 'none'} if data_type != 'average' or xAxis != 'phase' else {}
    avg_group2_style = {
        'display': 'none'} if data_type != 'average' or xAxis == 'phase' else {}
    return avg_group_style, avg_group1_style, avg_group2_style


@dash_app.callback(
    Output('errorControl', 'style'),
    Output('xAxisControl', 'style'),
    Output('plotTypeControl', 'style'),
    Input("url", "pathname")
)
def adjust_sidebar_content(pathname):
    errorControl_style = {'display': 'none'} if (
        pathname == "/noise" or pathname == "/matrix") else {}
    xAxisControl_style = {'display': 'none'} if pathname == "/matrix" else {}
    plotTypeControl_style = {
        'display': 'none'} if pathname == "/matrix" else {}
    return errorControl_style, xAxisControl_style, plotTypeControl_style

# navbar


@dash_app.callback(
    Output("modal", "is_open"),
    [Input("settings-link", "n_clicks"), Input("close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@dash_app.callback(
    [Output("2d-plot-link", "active"),
     Output("matrix-link", "active"),
     Output("noise-link", "active")],
    [Input("url", "pathname")]
)
def toggle_active_links(pathname):
    return [pathname == "/", pathname == "/matrix", pathname == "/noise"]


@dash_app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


# content

# Extract epoch information and sort points accordingly
def extract_epoch(filename):
    match = re.search(r"epoch(\d+)", filename)
    if match:
        return int(match.group(1))  # Extract numeric epoch if found
    # Use infinity if no epoch is found, so it sorts last
    return float('inf')


def process_points(pt, type, tooltipFontSize, thumnailsSize, dataSelection, annotation):
    children = []
    img_data = {}
    imglist = []
    bbox = pt.get("bbox", None)
    curveNumber = pt.get("curveNumber", None)
    pointIndex = pt.get("pointIndex", None)
    customdata = pt["customdata"]
    phase, wavetype = customdata.get("phase"), customdata.get("type")
    phase, wavetype, r_in, r_out = customdata.get("phase"), customdata.get(
        "type"), customdata.get("r_in"), customdata.get("r_out")
    # fig_anno_index = f"{wavetype}_{phase}"
    # point_index = f"c{curveNumber}pid{pointIndex}"
    point_index = f"{wavetype}_{phase}"
    # point_index = f"{wavetype}_{phase}_{r_in}_{r_out}"

    if "datatype" in customdata:
        return False, bbox, []

    img_src = f"https://via.placeholder.com/150?text={'Not exist'}"
    if "filename" in customdata:
        filename = customdata["filename"]
        # Extract values, ensuring they are properly formatted
        y_value = pt.get("y", "N/A")
        mjd_value = customdata.get("mjd", "N/A")
        time_value = customdata.get("time", "N/A")
        phase_value = customdata.get("phase", "N/A")
        wavetype = customdata.get("type", "N/A")
        # Create a formatted string for each
        y_text = f'Y-Axis: {y_value:,.5f}'
        mjd_text = f'MJD: {mjd_value:,.5f}' if isinstance(
            mjd_value, (float, int)) else f'MJD: {mjd_value}'
        time_text = f'Time: {time_value}'
        phase_text = f'Phase: {phase_value:,.3f}' if isinstance(
            phase_value, (float, int)) else f'Phase: {phase_value}'
        color = color_list[(curveNumber % len(
            dataSelection)) % len(color_list)]
        # Combine the paths
        file_path = f"{config.IMG_URI}{filename}"
        print(file_path)
        # Check if the file exists
        if filename not in imglist:
            imglist.append(filename)
            if Path(file_path).exists():
                img_src = file_path
            else:
                img_src = None

            img_data[img_src] = {
                'img_src': img_src,
                'mjd_text': mjd_text,
                'time_text': time_text,
                'type': wavetype,
                'phase_value': phase_value,
                'phase_text': phase_text,
                'point_index': point_index,
                'customdata': customdata,
                'filename': customdata.get('filename', 'N/A')
            }
        else:
            img_src = None

        if type == 'hover':
            fontSize = f'{tooltipFontSize}px'
            wh = f'{thumnailsSize}px'
            whd = 150
            if int(tooltipFontSize) >= 18:
                whd = 200
            if int(tooltipFontSize) >= 24:
                whd = 250
            if int(tooltipFontSize) >= 30:
                whd = 300
            whdiv = f'{whd}px'

            # Adjust sizes and spacing for a more compact layout
            children.append(
                html.Div([
                    # Smaller image or space
                    html.Img(src=img_src, style={
                        "width": wh, "height": wh, "objectFit": "cover"}) if img_src else html.Br(),
                    html.Div([
                        html.Span(style={"backgroundColor": color, "borderRadius": "50%",
                                         "display": "inline-block", "width": "8px", "height": "8px", "marginRight": "5px"}),
                        html.Div([
                            html.P(y_text, style={
                                "margin": "2px 0", "lineHeight": "1.1", "fontSize": fontSize}),  # Smaller text
                            html.P(mjd_text, style={
                                "margin": "2px 0", "lineHeight": "1.1", "fontSize": fontSize}),
                            html.P(time_text, style={
                                "margin": "2px 0", "lineHeight": "1.1", "fontSize": fontSize}),
                            html.P(phase_text, style={
                                "margin": "2px 0", "lineHeight": "1.1", "fontSize": fontSize})
                        ], style={"display": "flex", "flexDirection": "column", "justifyContent": "center"})
                    ], style={"display": "flex", "alignItems": "center"})
                ], style={'width': whdiv, 'white-space': 'normal', 'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center'})
            )
    if type == 'click':
        # print(annotation)
        # Create children elements based on the grouped data
        for img_src, data in img_data.items():
            mjd_text = data['mjd_text']
            time_text = data['time_text']
            wavetype = data['type']
            phase_value = data['phase_value']
            phase_text = data['phase_text']
            point_index = data['point_index']
            customdata = data['customdata']
            customdata_json = json.dumps(customdata)
            children.append(
                html.Div([
                            html.Button(DashIconify(icon="clarity:trash-line", width=20), id={'type': 'delete-btn', 'index': point_index}, n_clicks=0,
    style={
        'background-color': 'orange',
        'color': 'black',
        'border': 'none',
        'cursor': 'pointer',
        'position': 'absolute',
        'top': '5px',
        'right': '5px',
        'display': 'flex',  # Use flexbox for alignment
        'align-items': 'center',  # Center vertically
        'justify-content': 'center',  # Center horizontally
        'width': '30px',  # Set a specific width if necessary
        'height': '30px',  # Set a specific height if necessary
        'border-radius': '10%',
    }),
                    # html.Button('×', id={'type': 'delete-btn', 'index': point_index}, n_clicks=0, style={'background-color': '#FF8700',
                    #             'color': 'white', 'border': 'none', 'cursor': 'pointer', 'position': 'absolute', 'top': '5px', 'right': '5px'}),
                    html.Div(
                        annotation['text'],
                        style={
                            'position': 'absolute',
                            'top': '5px',  # Adjust as needed
                            'left': '5px',  # Adjust as needed
                            # Semi-transparent background
                            'background-color': 'rgba(0, 0, 0, 1)',
                            # 'background-color': 'rgba(0, 0, 0, 0.5)',
                            'color': 'white',
                            'padding': '2px 5px',
                            'border-radius': '3px',
                            'font-size': '12px',
                            'font-weight': 'bold'
                        }
                    ),
                    html.Img(
                        src=img_src,
                        style={'width': '150px', 'height': '150px',
                               'margin': '5px', 'cursor': 'pointer'},
                        id={'type': 'dynamic-img',
                            'index': point_index, 'src': img_src}
                    )
                ], style={'position': 'relative'},
                    id={'type': 'dynamic-div-img', 'index': point_index},
                    # Adding custom data attributes here
                    **{
                    'data-mjd-text': mjd_text,
                    'data-time-text': time_text,
                    'data-phase-value': phase_value,
                    'data-wave-type': wavetype,
                    'data-phase-text': phase_text,
                    'data-filename': customdata.get('filename', 'N/A'),
                    'data-img-src': img_src,
                    'data-point-index': point_index,
                    'data-customdata': customdata_json,
                }
                )
            )
    return True, bbox, children


@dash_app.callback(
    Output("graph-tooltip", "show"),
    Output("graph-tooltip", "bbox"),
    Output("graph-tooltip", "children"),
    Input("plot-chart", "hoverData"),
    State('tooltipFontSize', 'value'),
    State('thumnailsSize', 'value'),
    State('plot-chart', 'figure'),
    State('dataSelection', 'value'),
    State('dataType', 'value'),
    State("url", "pathname"),
)
def display_hover(hoverData, tooltipFontSize, thumnailsSize, current_fig, dataSelection, dataType, pathname):

    # Ensure that current_fig is not None and has a layout
    if current_fig is None:
        return False, dash.no_update, dash.no_update

    if hoverData is None or pathname == "matrix" or dataType == 'average':
        return False, dash.no_update, dash.no_update

    return process_points(hoverData["points"][0], 'hover', tooltipFontSize, thumnailsSize, dataSelection, [])


@dash_app.callback(
    Output('2d_plot', 'style'),
    Output('imageContent', 'style'),
    Output('matrix_plot', 'style'),
    Input("url", "pathname")
)
def render_page_content(pathname):
    if pathname == "/":
        return {'margin': '8px', 'display': 'block'}, {'margin': '8px', 'display': 'block'}, {'margin': '8px', 'display': 'none'}
    elif pathname == "/noise":
        return {'margin': '8px', 'display': 'block'}, {'margin': '8px', 'display': 'block'}, {'margin': '8px', 'display': 'none'}
    elif pathname == "/matrix":
        return {'margin': '8px', 'display': 'none'}, {'margin': '8px', 'display': 'none'}, {'margin': '8px', 'display': 'flex'}
    elif pathname == "/test":
        return html.P("Oh cool, this is test page!")
    # If the user tries to reach a different page, return a 404 message
    return html.Div(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ],
        className="p-3 bg-light rounded-3",
    )


@dash_app.callback(
    Output('plot-title', 'children'),
    Input('dataType', 'value'),
    Input("url", "pathname")
)
def update_plot_title(dataType, pathname):
    if pathname == "/":
        try:
            dataType_label = next(
                option['label'] for option in data_type_options if option['value'] == dataType)
            title_plot = f'ZTF J1539 PSF Light Curves: {dataType_label}'
        except StopIteration:
            title_plot = 'ZTF J1539 PSF Light Curves: Unknown Data Type'
        return title_plot
    elif pathname == "/noise":
        try:
            dataType_label = next(
                option['label'] for option in data_type_options if option['value'] == dataType)
            title_plot = f'ZTF J1539 PSF Signal-to-noise: {dataType_label}'
        except StopIteration:
            title_plot = 'ZTF J1539 PSF Signal-to-noise: Unknown Data Type'
        return title_plot
    elif pathname == "/matrix":
        try:
            dataType_label = next(
                option['label'] for option in data_type_options if option['value'] == dataType)
            title_plot = f'ZTF J1539 PSF Scatter Matrix Plots for SW and LW Data: {dataType_label}'
        except StopIteration:
            title_plot = 'ZTF J1539 PSF Scatter Matrix Plots for SW and LW Data: Unknown Data Type'
        return title_plot
    else:
        return ''


@dash_app.callback(
    Output('image-modal', 'is_open'),
    Output('modal-image', 'src'),
    Output('modal-details', 'children'),
    Output('value-store', 'data'),
    Output('plot-chart', 'figure'),
    Output('image-container', 'children'),
    Output('annotations-store', 'data'),
    Output('annotations-clicked', 'data'),
    Output('annotations-mapping', 'data'),
    Output('plot-chart', 'clickData'),
    Output('plot-chart', 'clickAnnotationData'),
    Input({'type': 'dynamic-img', 'index': dash.dependencies.ALL,
          'src': dash.dependencies.ALL}, 'n_clicks'),
    Input('close-modal', 'n_clicks'),
    Input({'type': 'delete-btn', 'index': dash.dependencies.ALL}, 'n_clicks'),
    Input('dataType', 'value'),
    Input('dataSelection', 'value'),
    Input('noOfBins', 'value'),
    Input('xAxis', 'value'),
    Input('errorBars', 'value'),
    Input('plotType', 'value'),
    Input('noOfDataPoint', 'value'),
    Input('legendFontSize', 'value'),
    Input('labelFontSize', 'value'),
    Input("url", "pathname"),
    Input('plot-chart', 'clickData'),
    Input('plot-chart', 'clickAnnotationData'),
    Input('pointSize', 'value'),
    Input('lineWidth', 'value'),
    State('value-store', 'data'),
    State('image-container', 'children'),
    State('image-modal', 'is_open'),
    State({'type': 'dynamic-img', 'index': dash.dependencies.ALL,
          'src': dash.dependencies.ALL}, 'n_clicks_timestamp'),
    State('plot-chart', 'figure'),
    State('dataSelection', 'value'),
    State('tooltipFontSize', 'value'),
    State('thumnailsSize', 'value'),
    State('annotations-store', 'data'),
    State('annotations-mapping', 'data'),
    State('annotations-clicked', 'data'),
)
def combined_callback(img_n_clicks, close_n_clicks, delete_n_clicks, dataType, dataSelectionInput, noOfBins, xAxis, errorBars, plotType,
                      noOfDataPoint, legendFontSize, labelFontSize, pathname, clickData, clickAnnotationData, pointSize, lineWidth,
                      data, children, is_open, timestamps, current_fig, dataSelectionState, tooltipFontSize, thumnailsSize,
                      annotations, annotation_mapping, anno_clicked):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, None, None, data, go.Figure(), children, annotations
    anno_click = anno_clicked
    is_anno_clicked = False
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    fig = go.Figure() if not current_fig else current_fig
    if children is None:
        children = []
    if annotation_mapping is None:
        annotation_mapping = {}
    imgsrc = None
    modal_details = None
    # print(clickData)
    # print(clickAnnotationData)
    if 'dynamic-img' in ctx.triggered[0]['prop_id'].split('.n_clicks')[0]:
        triggered_id = ctx.triggered[0]['prop_id'].split('.n_clicks')[0]
        valid_timestamps = [
            timestamp for timestamp in timestamps if timestamp is not None]
        if valid_timestamps:
            latest_click = max(valid_timestamps)
            latest_index = timestamps.index(latest_click)
            image_index = children[latest_index]['props']['id']['index']
            if eval(triggered_id)['index'] == image_index and latest_click > data:
                data = latest_click
                # Extract the custom data attributes
                for a in annotations:
                    if a["text"] == annotation_mapping[eval(triggered_id)['index']]:
                        a["bgcolor"] = 'rgba(0, 240, 255, 0.7)'
                        a["font"] = {"color": "black"}  # Change text color for visibility
                    else:
                        a["bgcolor"] = "black"
                        a["font"] = {"color": "white"}  # Keep other annotations readable
                fig['layout']['annotations'] = annotations

                for c in children:
                    if c.get('props', {}).get('id', {}).get('index') == eval(triggered_id)['index']:
                        if c.get('type') == 'Div' and c.get('props', {}).get('children'):
                            for child in c['props']['children']:
                                if child.get('type') == 'Div' and child.get('props', {}).get('children'):
                                    child['props']['style']['background-color'] = 'rgba(0, 240, 255, 0.7)'
                                    child['props']['style']['color'] = 'rgba(0, 0, 0, 1)'
                                    break
                    else:
                        if c.get('type') == 'Div' and c.get('props', {}).get('children'):
                            for child in c['props']['children']:
                                if child.get('type') == 'Div' and child.get('props', {}).get('children'):
                                    # child['props']['style']['background-color'] = 'rgba(0, 0, 0, 0.5)'
                                    child['props']['style']['background-color'] = 'rgba(0, 0, 0, 1)'
                                    child['props']['style']['color'] = 'rgba(255, 255, 255, 1)'
                                    break

                for child in children:
                    if child['props']['id']['index'] == image_index:
                        # Access the custom data attributes from `data-*`
                        mjd_text = child['props'].get('data-mjd-text', 'N/A')
                        time_text = child['props'].get('data-time-text', 'N/A')
                        phase_text = child['props'].get('data-phase-text', 'N/A')
                        phase_value = child['props'].get('data-phase-value', 'N/A')
                        wavetype = child['props'].get('data-wave-type', 'N/A')
                        filename_full = child['props'].get(
                            'data-filename', 'N/A')
                        img_src = child['props'].get('data-img-src', 'N/A')
                        point_index = child['props'].get(
                            'data-point-index', 'N/A')
                        color = child['props'].get('data-color', 'N/A')
                        # print(phase_value)
                        customdata_json = child['props'].get(
                            'data-customdata', '{}')
                        customdata = json.loads(
                            customdata_json) if customdata_json else {}

                        # Extract the filename and image slice
                        filename = filename_full.split(
                            '/')[-1].split('_slice')[0].replace('.png', '.fits')
                        image_slice = filename_full.split(
                            '_slice')[-1].split('.')[0]
                        # Common font size for consistency
                        common_font_size = "14px"
                        # Prepare modal details
                        modal_details = [
                            html.P(f"{mjd_text}", style={
                                   "margin": "2px 0", "lineHeight": "1.1", "fontSize": common_font_size}),
                            html.P(f"{time_text}", style={
                                   "margin": "2px 0", "lineHeight": "1.1", "fontSize": common_font_size}),
                            html.P(f"{phase_text}", style={
                                   "margin": "2px 0", "lineHeight": "1.1", "fontSize": common_font_size}),
                            html.P(f"Epoch: {customdata['epoch']}", style={
                                   "margin": "2px 0", "lineHeight": "1.1", "fontSize": common_font_size}),
                            html.P(f"Wave Type: {customdata['type']}", style={
                                   "margin": "2px 0", "lineHeight": "1.1", "fontSize": common_font_size}),
                            html.P(f"Filename: {filename}", style={
                                   "margin": "2px 0", "lineHeight": "1.1", "fontSize": common_font_size}),
                            html.P(f"Image Slice: {image_slice}", style={
                                   "margin": "2px 0", "lineHeight": "1.1", "fontSize": common_font_size}),
                            html.Br(),
                        ]
                        # print(dataSelectionState)
                        # Dynamically create HTML elements for each y_text and color in img_details
                        for color_index, trace in enumerate(current_fig['data']):
                            customdata_values = trace.get("customdata", [])
                            y = trace.get("y", [])
                            color_item = color_list[(color_index % int(len(current_fig['data'])/2)) % len(color_list)]
                            # Iterate over customdata to check for matching phase values
                            for i, customdata_point in enumerate(customdata_values):
                                if customdata_point.get("type") != wavetype:
                                    break
                                if customdata_point.get("phase") == phase_value:
                                    y_value = y[i]
                                    r_in = customdata_point.get('r_in', 'N/A')
                                    r_out = customdata_point.get('r_out', 'N/A')
                                    y_text_item = f'Y-Axis: {y_value:,.5f}'
                                    modal_details.append(
                                        html.Div([
                                            html.Span(
                                                style={"backgroundColor": color_item, "borderRadius": "50%",
                                                    "display": "inline-block", "width": "10px", "height": "10px", "marginRight": "5px"}
                                            ),
                                            html.P(f"(r_in: {r_in}, r_out: {r_out}) {y_text_item} ", style={
                                                "margin": "2px 0", "lineHeight": "1.1", "fontSize": common_font_size})
                                        ], style={"display": "flex", "alignItems": "center"})
                                    )
                                    break
                        # for detail in img_details:
                        #     y_text_item = detail.get('y_text', 'N/A')
                        #     color_item = detail.get('color', 'N/A')
                        #     r_in = detail.get('r_in', 'N/A')
                        #     r_out = detail.get('r_out', 'N/A')
                        #     modal_details.append(
                        #         html.Div([
                        #             html.Span(
                        #                 style={"backgroundColor": color_item, "borderRadius": "50%",
                        #                        "display": "inline-block", "width": "10px", "height": "10px", "marginRight": "5px"}
                        #             ),
                        #             html.P(f"(r_in: {r_in}, r_out: {r_out}) {y_text_item} ", style={
                        #                    "margin": "2px 0", "lineHeight": "1.1", "fontSize": common_font_size})
                        #         ], style={"display": "flex", "alignItems": "center"})
                        #     )
                        # break
                is_open = not is_open
                imgsrc = eval(triggered_id)['src'].replace(
                    "thumbnails", "full-size")
                # return is_open, imgsrc, modal_details, data

    elif 'close-modal' in ctx.triggered[0]['prop_id'].split('.n_clicks')[0]:
        is_open = not is_open
        # return is_open, imgsrc, modal_details, data

    elif pathname != '/matrix':
        if triggered_id == 'plot-chart' and clickAnnotationData:
            if annotation_mapping[clickAnnotationData["annotation"]["text"]] != anno_click:
                anno_click = annotation_mapping[clickAnnotationData["annotation"]["text"]]
                for a in annotations:
                    if a["text"] == clickAnnotationData["annotation"]["text"]:
                        a["bgcolor"] = 'rgba(0, 240, 255, 0.7)'
                        a["font"] = {"color": "black"}  # Change text color for visibility
                    else:
                        a["bgcolor"] = "black"
                        a["font"] = {"color": "white"}  # Keep other annotations readable

                for c in children:
                    if c.get('props', {}).get('id', {}).get('index') == anno_click:
                        if c.get('type') == 'Div' and c.get('props', {}).get('children'):
                            for child in c['props']['children']:
                                if child.get('type') == 'Div' and child.get('props', {}).get('children'):
                                    child['props']['style']['background-color'] = 'rgba(0, 240, 255, 0.7)'
                                    child['props']['style']['color'] = 'rgba(0, 0, 0, 1)'
                                    break
                    else:
                        if c.get('type') == 'Div' and c.get('props', {}).get('children'):
                            for child in c['props']['children']:
                                if child.get('type') == 'Div' and child.get('props', {}).get('children'):
                                    # child['props']['style']['background-color'] = 'rgba(0, 0, 0, 0.5)'
                                    child['props']['style']['background-color'] = 'rgba(0, 0, 0, 1)'
                                    child['props']['style']['color'] = 'rgba(255, 255, 255, 1)'
                                    break
                is_anno_clicked = True
                fig['layout']['annotations'] = annotations
        if not is_anno_clicked and triggered_id == 'plot-chart' and dataType == 'raw' and clickData:
            # print("1")
            pt = clickData['points'][0]
            curveNumber = pt.get("curveNumber")
            x, y, customdata = pt.get("x"), pt.get(
                "y"), pt.get("customdata", {})
            phase, wavetype, r_in, r_out = customdata.get("phase"), customdata.get(
                "type"), customdata.get("r_in"), customdata.get("r_out")
            xref, yref = ("x", "y") if curveNumber < len(
                dataSelectionInput) else ("x2", "y2")
            fig_anno_index = f"{wavetype}_{phase}"
            # fig_anno_index = f"{wavetype}_{phase}_{r_in}_{r_out}"
            clicked_phase = phase
            if annotations:
                try:
                    last_annotation = annotations[-1]
                    last_number = int(last_annotation['text'].split()[-1])
                    next_number = last_number + 1
                except (ValueError, IndexError):
                    next_number = 1
            else:
                next_number = 1
                if 'layout' not in current_fig['layout']:
                    current_fig['layout']['annotations'] = []
                annotations = current_fig['layout']['annotations']
            existing_ids = [key for key in annotation_mapping if 'No.' not in key]

            if fig_anno_index not in existing_ids:
                for trace in current_fig['data']:
                    customdata_values = trace.get("customdata", [])
                    # Iterate over customdata to check for matching phase values
                    for i, customdata_point in enumerate(customdata_values):
                        if customdata_point.get("type") != wavetype:
                            break
                        if customdata_point.get("phase") == clicked_phase:
                            # Create an annotation at the top for the matched phase
                            new_annotation = dict(
                                x=trace["x"][i],
                                y=trace["y"][i],  # Offset above max y for visibility
                                xref=xref,
                                yref=yref,
                                text=f"No. {next_number}",
                                showarrow=True,
                                arrowhead=7,
                                xanchor="center",
                                yanchor="bottom",
                                ax=0,
                                ay=-40,
                                font=dict(color='white', size=14),
                                bgcolor='black',
                                bordercolor='black',
                                borderwidth=2,
                                borderpad=4,
                                arrowcolor='black',
                                # id=fig_anno_index,
                                captureevents=True
                            )
                            annotation_mapping[fig_anno_index] = f"No. {next_number}"
                            annotation_mapping[f"No. {next_number}"] = fig_anno_index
                            # Add the annotation
                            annotations.append(new_annotation)
                next_number += 1
                # annotations.append(new_annotation)
                fig['layout']['annotations'] = annotations

                cond, bbox, new_children = process_points(
                    pt, 'click', tooltipFontSize, thumnailsSize, dataSelectionState, new_annotation)
                if cond:
                    children += new_children
            else:
                # print(fig_anno_index)
                for a in annotations:
                    if a["text"] == annotation_mapping[fig_anno_index]:
                        a["bgcolor"] = 'rgba(0, 240, 255, 0.7)'
                        a["font"] = {"color": "black"}  # Change text color for visibility
                    else:
                        a["bgcolor"] = "black"
                        a["font"] = {"color": "white"}  # Keep other annotations readable
                fig['layout']['annotations'] = annotations

                for c in children:
                    if c.get('props', {}).get('id', {}).get('index') == fig_anno_index:
                        if c.get('type') == 'Div' and c.get('props', {}).get('children'):
                            for child in c['props']['children']:
                                if child.get('type') == 'Div' and child.get('props', {}).get('children'):
                                    child['props']['style']['background-color'] = 'rgba(0, 240, 255, 0.7)'
                                    child['props']['style']['color'] = 'rgba(0, 0, 0, 1)'
                                    break
                    else:
                        if c.get('type') == 'Div' and c.get('props', {}).get('children'):
                            for child in c['props']['children']:
                                if child.get('type') == 'Div' and child.get('props', {}).get('children'):
                                    # child['props']['style']['background-color'] = 'rgba(0, 0, 0, 0.5)'
                                    child['props']['style']['background-color'] = 'rgba(0, 0, 0, 1)'
                                    child['props']['style']['color'] = 'rgba(255, 255, 255, 1)'
                                    break
        elif not is_anno_clicked and triggered_id in ['legendFontSize', 'labelFontSize', 'pointSize', 'lineWidth']:
            for trace in fig["data"]:
                trace["marker"]['size'] = pointSize
                trace["line"]['width'] = lineWidth
            # print("2")
            fig['layout']['font']['size'] = labelFontSize
            fig['layout']['legend']['font']['size'] = legendFontSize
        elif not is_anno_clicked and 'delete-btn' in ctx.triggered[0]['prop_id'].split('.n_clicks')[0]:
            # print("3")
            triggered_id = ctx.triggered[0]['prop_id'].split('.n_clicks')[0]
            text_to_remove = annotation_mapping[eval(triggered_id)['index']]
            new_child_list = []
            del annotation_mapping[text_to_remove]
            del annotation_mapping[eval(triggered_id)['index']]
            for c in children:
                if c.get('props', {}).get('id', {}).get('index') != eval(triggered_id)['index']:
                    new_child_list.append(c)
            children = new_child_list
            # annotations = [a for a in annotations if a['id'] != eval(triggered_id)['index']]
            annotations = [a for a in annotations if a['text'] != text_to_remove]
            fig['layout']['annotations'] = annotations
        elif not is_anno_clicked:
            # print("4")
            SW_traces = update_trace('SW', dataType, dataSelectionInput,
                                     noOfBins, xAxis, errorBars, plotType, noOfDataPoint, pathname, pointSize, lineWidth)
            LW_traces = update_trace('LW', dataType, dataSelectionInput,
                                     noOfBins, xAxis, errorBars, plotType, noOfDataPoint, pathname, pointSize, lineWidth)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02,
                                # x_title=next(
                                #     option['label'] for option in xAxis_options if option['value'] == xAxis),
                                # y_title='Surface Brightness (MJy/sr)' if pathname != "/noise" else 'Signal-to-noise ratio'
                                )

            for trace in SW_traces:
                fig.add_trace(trace, row=1, col=1)
            for trace in LW_traces:
                fig.add_trace(trace, row=2, col=1)

            if dataType == 'average' and xAxis == 'phase':
                bin_edges = np.linspace(0, 2, noOfBins + 1)
                colors = ["lightblue", "lightgray"]
                shapes = [{'type': 'rect', 'x0': bin_edges[i], 'x1': bin_edges[i + 1], 'y0': 0, 'y1': 1, 'xref': 'x', 'yref': 'paper',
                           'fillcolor': colors[i % len(colors)], 'opacity': 0.2, 'line': {'width': 0}} for i in range(noOfBins)]
                fig.update_layout(shapes=shapes)
            fig.update_layout(
                height=800,
                showlegend=True,
                legend=dict(
                    font=dict(size=legendFontSize),
                    groupclick="toggleitem"  # Group click behavior
                ),
                font=dict(size=labelFontSize),
                hovermode="closest"
            )
            fig.update_xaxes(
                # tickangle = 90,
                title_text = next(option['label'] for option in xAxis_options if option['value'] == xAxis),
                title_font = {"size": 20},
                title_standoff = 10,
                row=2, col=1)
            
            # Surface Brightness (MJy/sr), Signal-to-noise ratio
            fig.update_yaxes(
                title_text = 'SW: Surf Bright (MJy/sr)' if pathname != "/noise" else 'SW: S/N Ratio',
                title_standoff = 10,
                row=1, col=1)
            fig.update_yaxes(
                title_text = 'LW: Surf Bright (MJy/sr)' if pathname != "/noise" else 'LW: S/N Ratio',
                title_standoff = 10,
                row=2, col=1)
            if len(fig["data"]) <= 0:
                annotations = []
                children = []
                annotation_mapping = {}
                anno_click = ""
            else:
                new_annotation_list = []
                new_next_number = 1
                existing_ids = [key for key in annotation_mapping if 'No.' not in key]
                for ex_id in existing_ids:
                    wavetype, clicked_phase = ex_id.split('_')
                    
                    for trace in fig['data']:
                        # print(trace)
                        if trace["legendgroup"] == wavetype:
                            xref = trace["xaxis"]
                            yref = trace["yaxis"]
                            # print(xref,yref)
                            customdata_values = trace["customdata"] if hasattr(trace, 'customdata') else []
                            # Iterate over customdata to check for matching phase values
                            for i, customdata_point in enumerate(customdata_values):
                                if str(customdata_point.get("phase")) == clicked_phase:
                                    # print("found", new_next_number)
                                    # Create an annotation at the top for the matched phase
                                    new_annotation = dict(
                                        x=trace["x"][i],
                                        y=trace["y"][i],  # Offset above max y for visibility
                                        xref=xref,
                                        yref=yref,
                                        text=annotation_mapping[ex_id],
                                        showarrow=True,
                                        arrowhead=7,
                                        xanchor="center",
                                        yanchor="bottom",
                                        ax=0,
                                        ay=-40,
                                        font=dict(color='white', size=14),
                                        bgcolor='black',
                                        bordercolor='black',
                                        borderwidth=2,
                                        borderpad=4,
                                        arrowcolor='black',
                                        # id=ex_id,
                                        captureevents=True
                                    )
                                    if ex_id == anno_click:
                                        new_annotation["bgcolor"] = 'rgba(0, 240, 255, 0.7)'
                                    fig.add_annotation(new_annotation)
                                    # Add the annotation
                                    new_annotation_list.append(new_annotation)
                    new_next_number += 1
                # print(new_annotation_list)
                # fig.update_layout(annotations=new_annotation_list) 
                annotations = new_annotation_list

            if triggered_id in ['dataType', 'url']:
                children = []
    # fig.update_layout(template="plotly_dark")
    return is_open, imgsrc, modal_details, data, fig, children, annotations, anno_click, annotation_mapping, None, None


@dash_app.callback(
    Output('dropdown-message', 'children'),
    Output('xAxis', 'value'),
    Output('scatter-matrix-sw', 'figure'),
    Output('scatter-matrix-lw', 'figure'),
    Input('dataType', 'value'),
    Input('dataSelection', 'value'),
    Input('noOfBins', 'value'),
    Input('errorBars', 'value'),
    Input('xAxis', 'value'),
    Input('plotType', 'value'),
    Input('noOfDataPoint', 'value'),
    Input("url", "pathname"),
    Input('labelFontSize', 'value'),
    State('scatter-matrix-sw', 'figure'),
    State('scatter-matrix-lw', 'figure'),
)
def update_matrix(dataType, dataSelection, noOfBins, errorBars, xAxis, plotType, noOfDataPoint, pathname, labelFontSize,fig_sw, fig_lw):
    # Return empty figures if the pathname doesn't match    
    ctx = dash.callback_context
    if not ctx.triggered:
        return '', 'mjd', empty_fig, empty_fig
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    empty_fig = go.Figure()
    if pathname == "/matrix":
        if not dataSelection or len(dataSelection) < 2:
            return 'Please select at least 2 options.', 'mjd', empty_fig, empty_fig
        epochs = [get_epoch(value) for value in dataSelection]
        if len(set(epochs)) > 1:
            return 'Please select options from the same epoch.', 'mjd', empty_fig, empty_fig
        elif triggered_id in ['labelFontSize']:
            print(fig_sw['layout'])
            fig_sw['layout']['font']['size'] = labelFontSize
            fig_lw['layout']['font']['size'] = labelFontSize
            return '', 'mjd', fig_sw, fig_lw
        else:
            df_SW = update_df('SW', dataType, dataSelection,
                              plotType, noOfDataPoint)
            df_LW = update_df('LW', dataType, dataSelection,
                              plotType, noOfDataPoint)
            fig1 = px.scatter_matrix(df_SW, dimensions=list(df_SW.columns), labels={
                col: col.replace('_', ' ') for col in df_SW.columns})
            fig1.update_traces(diagonal_visible=False)
            fig2 = px.scatter_matrix(df_LW, dimensions=list(df_LW.columns), labels={
                col: col.replace('_', ' ') for col in df_LW.columns})
            fig2.update_traces(diagonal_visible=False)
            # Update layout for SW plots
            fig1.update_layout(title='SW Scatter Matrix', height=600, showlegend=True, legend=dict(
                groupclick="toggleitem"), hovermode="x", font=dict(size=labelFontSize))
            fig1.update_traces(marker_line=dict(
                width=0.1, color="black"), opacity=0.9)

            # Update layout for LW plots
            fig2.update_layout(title='LW Scatter Matrix', height=600, showlegend=True, legend=dict(
                groupclick="toggleitem"), hovermode="x", font=dict(size=labelFontSize))
            fig2.update_traces(marker_line=dict(
                width=0.1, color="black"), opacity=0.9)

            return '', 'mjd', fig1, fig2
    return '', xAxis, empty_fig, empty_fig


if __name__ == "__main__":
    # dash_app.run_server(debug=True)
    # dash_app.run_server(debug=True, port=8080, host='127.0.0.1') 
    dash_app.run_server(debug=True, port=8080, host='0.0.0.0') 
