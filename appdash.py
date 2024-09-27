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
# import h5py
import copy
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from astropy.time import Time
from astropy import units as u, constants as c
from components import data_type_options, get_epoch, xAxis_options, rawdata, dataList, sidebar, navbar, content, update_trace, update_df, modal

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


# @dash_app.callback(
#     Output('dropdown-message', 'children'),
#     Output('xAxis', 'value'),
#     Input('dataSelection', 'value'),
#     Input("url", "pathname"),
#     Input('xAxis', 'value'),
# )
# def check_minimum_values(selected_values, pathname, xAxis):
#     if pathname == "/matrix":
#         if not selected_values or len(selected_values) < 2:
#             return 'Please select at least 2 options.', 'mjd'
#         epochs = [get_epoch(value) for value in selected_values]
#         if len(set(epochs)) > 1:
#             return 'Please select options from the same epoch.', 'mjd'
#         else:
#             return '', 'mjd'
#     else:
#         return '', xAxis


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
@dash_app.callback(
    Output('2d_plot', 'style'),
    Output('imageContent', 'style'),
    Output('matrix_plot', 'style'),
    Input("url", "pathname")
)
def render_page_content(pathname):
    if pathname == "/":
        return {"height": "50vh", 'margin': '8px', 'display': 'block'},{"height": "35vh", 'margin': '8px', 'display': 'block'}, {"height": "50vh", 'margin': '8px', 'display': 'none'}
    elif pathname == "/noise":
        return {"height": "50vh", 'margin': '8px', 'display': 'block'},{"height": "35vh", 'margin': '8px', 'display': 'none'}, {"height": "50vh", 'margin': '8px', 'display': 'none'}
    elif pathname == "/matrix":
        return {"height": "50vh", 'margin': '8px', 'display': 'none'},{"height": "35vh", 'margin': '8px', 'display': 'none'}, {"height": "50vh", 'margin': '8px', 'display': 'flex'}
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
    Input('dataType', 'value'),
    Input('dataSelection', 'value'),
    Input('noOfBins', 'value'),
    Input('xAxis', 'value'),
    Input('errorBars', 'value'),
    Input('plotType', 'value'),
    Input('noOfDataPoint', 'value'),
    Input('legendFontSize', 'value'),
    Input('labelFontSize', 'value'),
    Input("url", "pathname")
)
def update_plot(dataType, dataSelection, noOfBins, xAxis, errorBars, plotType, noOfDataPoint, legendFontSize, labelFontSize, pathname):
    if pathname == "/" or pathname == "/noise":
        SW_traces = update_trace('SW', dataType, dataSelection, noOfBins,
                                 xAxis, errorBars, plotType, noOfDataPoint, pathname)
        LW_traces = update_trace('LW', dataType, dataSelection, noOfBins,
                                 xAxis, errorBars, plotType, noOfDataPoint, pathname)
        y_title = 'Surface Brightness (MJy/sr)'
        if pathname == "/noise":
            y_title = 'Signal-to-noise ratio'
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02,
                            x_title=next(option['label'] for option in xAxis_options if option['value'] == xAxis), y_title=y_title)
        # Add SW traces to subplot
        for trace in SW_traces:
            fig.add_trace(trace, row=1, col=1)

        # Add LW traces to subplot
        for trace in LW_traces:
            fig.add_trace(trace, row=2, col=1)

        if dataType == 'average' and xAxis == 'phase':
            # if dataType == 'average':
            # Precompute bin edges and the number of colors
            bin_edges = np.linspace(0, 2, noOfBins + 1)
            colors = ["lightblue", "lightgray"]
            num_colors = len(colors)

            # Create all vertical highlight sections
            shapes = [
                {
                    'type': 'rect',
                    'x0': bin_edges[i],
                    'x1': bin_edges[i + 1],
                    'y0': 0,
                    'y1': 1,
                    'xref': 'x',
                    'yref': 'paper',
                    'fillcolor': colors[i % num_colors],
                    'opacity': 0.2,
                    'line': {
                        'width': 0,
                    },
                }
                for i in range(noOfBins)
            ]
            fig.update_layout(shapes=shapes)
        fig.update_annotations(font_size=labelFontSize)
        fig.update_layout(
            height=800,
            showlegend=True,
            legend=dict(
                font=dict(size=legendFontSize),
                groupclick="toggleitem",
                grouptitlefont=dict(size=legendFontSize)
            ),
            legend_tracegroupgap=200,
            hovermode="x unified",
            font=dict(
                size=labelFontSize,
            )
            # transition={
            #         'duration': 500,
            #         'easing': 'cubic-in-out'
            # },
        )
        # fig.update_traces(
        #     marker_line=dict(width=0.1, color="black"),
        #     opacity=0.9,
        # )
        return fig
    return go.Figure()


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
                groupclick="toggleitem"), hovermode="x unified")
            fig1.update_traces(marker_line=dict(
                width=0.1, color="black"), opacity=0.9)

            # Update layout for LW plots
            fig2.update_layout(title='LW Scatter Matrix', height=600, showlegend=True, legend=dict(
                groupclick="toggleitem"), hovermode="x unified")
            fig2.update_traces(marker_line=dict(
                width=0.1, color="black"), opacity=0.9)

            return '', 'mjd', fig1, fig2
    return '', xAxis, empty_fig, empty_fig


if __name__ == "__main__":
    dash_app.run_server(debug=True)
    # app.run_server(debug=True, port=8080, host='0.0.0.0') # Or replace with the actual IP address of the machine
