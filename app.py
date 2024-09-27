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
from components import data_type_options, get_epoch, xAxis_options, color_list, sidebar, navbar, content, update_trace, update_df, modal

dash_app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app = dash_app.server

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


def process_points(points, type, tooltipFontSize, thumnailsSize, dataSelection):
    children = []
    img_data = {}
    imglist = []
    bbox = None
    for pt in points:
        bbox = pt.get("bbox", None)
        curveNumber = pt.get("curveNumber", None)
        pointIndex = pt.get("pointIndex", None)
        customdata = pt["customdata"]
        point_index = f"c{curveNumber}pid{pointIndex}"

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
            file_path = f"./static/img/thumbnails/{filename}"
            # Check if the file exists
            if Path(file_path).exists():
                if filename not in imglist:
                    imglist.append(filename)
                    img_src = file_path
                    img_data[img_src] = {
                        'img_src': img_src,
                        'mjd_text': mjd_text,
                        'time_text': time_text,
                        'phase_text': phase_text,
                        'point_index': point_index,
                        'customdata': customdata,
                        'filename': customdata.get('filename', 'N/A')
                    }
                    img_data[img_src]['img_details'] = []
                    img_data[file_path]['img_details'].append({
                        'y_text': y_text,
                        'color': color,
                        'r_in': customdata["r_in"],
                        'r_out': customdata["r_out"],
                    })
                else:
                    img_src = None
                    img_data[file_path]['img_details'].append({
                        'y_text': y_text,
                        'color': color,
                        'r_in': customdata["r_in"],
                        'r_out': customdata["r_out"],
                    })
            else:
                if filename not in imglist:
                    imglist.append(filename)
                    img_data[img_src] = {
                        'img_src': img_src,
                        'mjd_text': mjd_text,
                        'time_text': time_text,
                        'phase_text': phase_text,
                        'point_index': point_index,
                        'customdata': customdata,
                        'filename': customdata.get('filename', 'N/A')
                    }
                    img_data[img_src]['img_details'] = []
                    img_data[img_src]['img_details'].append({
                        'y_text': y_text,
                        'color': color,
                        'r_in': customdata["r_in"],
                        'r_out': customdata["r_out"],
                    })
                else:
                    img_data[img_src]['img_details'].append({
                        'y_text': y_text,
                        'color': color,
                        'r_in': customdata["r_in"],
                        'r_out': customdata["r_out"],
                    })
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
        # Create children elements based on the grouped data
        for img_src, data in img_data.items():
            mjd_text = data['mjd_text']
            time_text = data['time_text']
            phase_text = data['phase_text']
            point_index = data['point_index']
            img_details = data['img_details']
            customdata = data['customdata']
            img_details_json = json.dumps(img_details)
            customdata_json = json.dumps(customdata)
            children.append(
                html.Div([
                    html.Button('×', id={'type': 'delete-btn', 'index': point_index}, n_clicks=0, style={'background-color': 'red',
                                                                                                         'color': 'white', 'border': 'none', 'cursor': 'pointer', 'position': 'absolute', 'top': '5px', 'right': '5px'}),
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
                    'data-img-details': img_details_json,
                    'data-mjd-text': mjd_text,
                    'data-time-text': time_text,
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
    [Output("graph-tooltip", "show"),
     Output("graph-tooltip", "bbox"),
     Output("graph-tooltip", "children")],
    [Input("plot-chart", "hoverData"),
     Input('tooltipFontSize', 'value'),
     Input('thumnailsSize', 'value'),],
    State('dataSelection', 'value'),
    State('dataType', 'value'),
    State("url", "pathname"),
)
def display_hover(hoverData, tooltipFontSize, thumnailsSize, dataSelection, dataType, pathname):
    if hoverData is None or pathname == "matrix" or dataType == 'average':
        return False, dash.no_update, dash.no_update
    # Sort hoverData["points"] by "curveNumber"
    sorted_points = sorted(hoverData["points"], key=lambda pt: pt.get(
        "curveNumber", 0), reverse=False)

    # Group points by filename presence and sort by epoch
    points_with_filenames = [
        pt for pt in sorted_points if "filename" in pt["customdata"]]
    points_with_filenames.sort(
        key=lambda pt: extract_epoch(pt["customdata"]["filename"]))

    points_without_filenames = [
        pt for pt in sorted_points if "filename" not in pt["customdata"]]
    # Concatenate lists
    all_points = points_with_filenames + points_without_filenames
    # Process each sorted point

    return process_points(all_points, 'hover', tooltipFontSize, thumnailsSize, dataSelection)


@dash_app.callback(
    Output('image-modal', 'is_open'),
    Output('modal-image', 'src'),
    Output('modal-details', 'children'),  # Add output for modal details
    Output('value-store', 'data'),
    Input({'type': 'dynamic-img', 'index': dash.dependencies.ALL,
          'src': dash.dependencies.ALL}, 'n_clicks'),
    Input('close-modal', 'n_clicks'),
    State('value-store', 'data'),
    State('image-container', 'children'),
    State('image-modal', 'is_open'),
    State({'type': 'dynamic-img', 'index': dash.dependencies.ALL,
          'src': dash.dependencies.ALL}, 'n_clicks_timestamp')
)
def toggle_modal(img_n_clicks, close_n_clicks, data, children, is_open, timestamps):
    ctx = dash.callback_context

    if not ctx.triggered:
        return is_open, None, None, data

    triggered_id = ctx.triggered[0]['prop_id'].split('.n_clicks')[0]
    # print(triggered_id)
    if 'dynamic-img' in triggered_id:
        valid_timestamps = [
            timestamp for timestamp in timestamps if timestamp is not None]
        if valid_timestamps:
            latest_click = max(valid_timestamps)
            latest_index = timestamps.index(latest_click)
            image_index = children[latest_index]['props']['id']['index']
            if eval(triggered_id)['index'] == image_index and latest_click > data:
                data = latest_click

                # Extract the custom data attributes
                for child in children:
                    if child['props']['id']['index'] == image_index:
                        # Access the custom data attributes from `data-*`
                        mjd_text = child['props'].get('data-mjd-text', 'N/A')
                        time_text = child['props'].get('data-time-text', 'N/A')
                        phase_text = child['props'].get(
                            'data-phase-text', 'N/A')
                        filename_full = child['props'].get(
                            'data-filename', 'N/A')
                        img_src = child['props'].get('data-img-src', 'N/A')
                        point_index = child['props'].get(
                            'data-point-index', 'N/A')
                        color = child['props'].get('data-color', 'N/A')

                        # Retrieve and deserialize JSON attributes if they exist
                        img_details_json = child['props'].get(
                            'data-img-details', '[]')
                        img_details = json.loads(
                            img_details_json) if img_details_json else []
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

                        # Dynamically create HTML elements for each y_text and color in img_details
                        for detail in img_details:
                            y_text_item = detail.get('y_text', 'N/A')
                            color_item = detail.get('color', 'N/A')
                            r_in = detail.get('r_in', 'N/A')
                            r_out = detail.get('r_out', 'N/A')
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
                return not is_open, eval(triggered_id)['src'].replace("thumbnails", "full-size"), modal_details, data

    elif 'close-modal' in triggered_id:
        return not is_open, None, None, data

    return is_open, None, None, data


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
    Output('plot-chart', 'figure'),
    Output('image-container', 'children'),
    Output('annotations-store', 'data'),  # Update annotations store
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
    State('plot-chart', 'figure'),
    State('dataSelection', 'value'),
    State('image-container', 'children'),
    State('tooltipFontSize', 'value'),
    State('thumnailsSize', 'value'),
    State('annotations-store', 'data')  # Get current annotations from store
)
def update_plot(n_clicks_list, dataType, dataSelectionInput, noOfBins, xAxis, errorBars, plotType, noOfDataPoint,
                legendFontSize, labelFontSize, pathname, clickData, current_fig, dataSelectionState, children,
                tooltipFontSize, thumnailsSize, annotations):
    ctx = dash.callback_context
    if not ctx.triggered:
        return go.Figure(), children, annotations
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print(triggered_id)

    # Initialize children if it's None
    if children is None:
        children = []

    # Initialize annotations if None
    if annotations is None:
        annotations = []

    if triggered_id == 'plot-chart' and pathname != '/matrix' and dataType == 'raw':
        if clickData:
            points_with_filenames = [
                pt for pt in clickData["points"] if "filename" in pt["customdata"]]
            points_without_filenames = [
                pt for pt in clickData["points"] if "filename" not in pt["customdata"]]

            points_with_filenames.sort(
                key=lambda pt: extract_epoch(pt["customdata"]["filename"]))

            all_points = points_with_filenames + points_without_filenames

            cond, bbox, new_children = process_points(
                all_points, 'click', tooltipFontSize, thumnailsSize, dataSelectionState)
            
            if cond:
                # Add new children to the existing list
                children = children + new_children

    elif triggered_id in ['dataType', 'url']:
        children = []
    elif triggered_id not in ['dataSelection']:
        # Remove specific children based on 'index'
        children = [c for c in children if c.get('props', {}).get('id', {}).get('index') != eval(triggered_id)['index']]

    if pathname == "/" or pathname == "/noise":
        if triggered_id == 'plot-chart' and clickData and dataType == 'raw':
            point_index = clickData['points'][0]['pointIndex']
            x = clickData['points'][0]['x']
            y = clickData['points'][0]['y']
            curve_number = clickData['points'][0]['curveNumber']

            if curve_number < len(dataSelectionInput):
                xref, yref = "x", "y"  # Top subplot
            else:
                xref, yref = "x2", "y2"  # Bottom subplot

            new_annotation = dict(
                x=x,
                y=y,
                xref=xref,
                yref=yref,
                text=f"No. {len(annotations)+1}",  # Use the length of stored annotations
                showarrow=True,
                arrowhead=7,
                xanchor="center",
                yanchor="bottom",
                ax=0,
                ay=-40,
                font=dict(color='red'),
                arrowcolor='red'
            )

            # Append new annotation to the stored list
            annotations.append(new_annotation)

            # current_fig['layout'].setdefault('annotations', []).append(new_annotation)
            current_fig['layout']['annotations'] = annotations
            return current_fig, children, annotations

        elif triggered_id in ['legendFontSize', 'labelFontSize']:
            current_fig['layout']['font']['size'] = labelFontSize
            current_fig['layout']['legend']['font']['size'] = legendFontSize
            return current_fig, children, annotations

        else:
            SW_traces = update_trace('SW', dataType, dataSelectionInput, noOfBins,
                                     xAxis, errorBars, plotType, noOfDataPoint, pathname)
            LW_traces = update_trace('LW', dataType, dataSelectionInput, noOfBins,
                                     xAxis, errorBars, plotType, noOfDataPoint, pathname)
            
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02,
                                x_title=next(option['label'] for option in xAxis_options if option['value'] == xAxis),
                                y_title='Surface Brightness (MJy/sr)' if pathname != "/noise" else 'Signal-to-noise ratio')

            for trace in SW_traces:
                fig.add_trace(trace, row=1, col=1)
            for trace in LW_traces:
                fig.add_trace(trace, row=2, col=1)

            if dataType == 'average' and xAxis == 'phase':
                bin_edges = np.linspace(0, 2, noOfBins + 1)
                colors = ["lightblue", "lightgray"]
                shapes = [
                    {'type': 'rect', 'x0': bin_edges[i], 'x1': bin_edges[i + 1], 'y0': 0, 'y1': 1, 'xref': 'x', 'yref': 'paper',
                     'fillcolor': colors[i % len(colors)], 'opacity': 0.2, 'line': {'width': 0}} for i in range(noOfBins)
                ]
                fig.update_layout(shapes=shapes)

            fig.update_layout(
                height=800,
                showlegend=True,
                legend=dict(font=dict(size=legendFontSize), groupclick="toggleitem", grouptitlefont=dict(size=legendFontSize)),
                font=dict(size=labelFontSize),
                hovermode="closest"
            )
            fig['layout']['annotations'] = annotations
            return fig, children, annotations

    return go.Figure(), children, annotations  # Return empty figure if pathname doesn't match


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
    Input("url", "pathname")
)
def update_matrix(dataType, dataSelection, noOfBins, errorBars, xAxis, plotType, noOfDataPoint, pathname):
    # Return empty figures if the pathname doesn't match
    empty_fig = go.Figure()
    if pathname == "/matrix":
        if not dataSelection or len(dataSelection) < 2:
            return 'Please select at least 2 options.', 'mjd', empty_fig, empty_fig
        epochs = [get_epoch(value) for value in dataSelection]
        if len(set(epochs)) > 1:
            return 'Please select options from the same epoch.', 'mjd', empty_fig, empty_fig
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
                groupclick="toggleitem"), hovermode="x")
            fig1.update_traces(marker_line=dict(
                width=0.1, color="black"), opacity=0.9)

            # Update layout for LW plots
            fig2.update_layout(title='LW Scatter Matrix', height=600, showlegend=True, legend=dict(
                groupclick="toggleitem"), hovermode="x")
            fig2.update_traces(marker_line=dict(
                width=0.1, color="black"), opacity=0.9)

            return '', 'mjd', fig1, fig2
    return '', xAxis, empty_fig, empty_fig


if __name__ == "__main__":
    dash_app.run_server(debug=True)
    # app.run_server(debug=True, port=8080, host='0.0.0.0') # Or replace with the actual IP address of the machine
