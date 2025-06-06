import dash
import json
import numpy as np
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from utils import extract_epoch, process_points
from dash import dcc, html, callback_context
from plotly.subplots import make_subplots

from components import data_type_options, get_epoch, xAxis_options, color_list, sidebar, navbar, content, update_trace, update_df, modal


def register_graph_callbacks(app):
    @app.callback(
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


    @app.callback(
        Output('2d_plot', 'style'),
        Output('imageContent', 'style'),
        Output('matrix_plot', 'style'),
        Output('image-plot', 'style'),
        Input("url", "pathname"),
        Input('dataType', 'value'),
    )
    def render_page_content(pathname, dataType):
        if pathname == "/":
            if dataType == 'average':
                return {'margin': '8px', 'display': 'block'}, {'margin': '8px', 'display': 'block'}, {'margin': '8px', 'display': 'none'}, {'margin': '8px', 'display': 'block'},
            else:
                return {'margin': '8px', 'display': 'block'}, {'margin': '8px', 'display': 'block'}, {'margin': '8px', 'display': 'none'}, {'margin': '8px', 'display': 'none'}
        elif pathname == "/noise":
            return {'margin': '8px', 'display': 'block'}, {'margin': '8px', 'display': 'block'}, {'margin': '8px', 'display': 'none'}, {'margin': '8px', 'display': 'none'}
        elif pathname == "/matrix":
            return {'margin': '8px', 'display': 'none'}, {'margin': '8px', 'display': 'none'}, {'margin': '8px', 'display': 'flex'}, {'margin': '8px', 'display': 'none'}
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



    @app.callback(
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


    @app.callback(
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
        # print("imgsrc", imgsrc)
        return is_open, imgsrc, modal_details, data, fig, children, annotations, anno_click, annotation_mapping, None, None

