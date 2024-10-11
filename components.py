import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, callback_context
from db import get_db, close_db, fetching_data, get_data

import math
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
import pandas as pd

# isDB = False
isDB = True
rawdata, dataList, data_for_df = fetching_data('ZTF_J1539', isDB)
data_type_options = [
    {'label': 'Average Data', 'value': 'average'},
    {'label': 'Raw Data', 'value': 'raw'},
]
xAxis_options = [
    {'label': 'Phase', 'value': 'phase'},
    {'label': 'MJD', 'value': 'mjd'},
    {'label': 'Datetime', 'value': 'time'},
    {'label': 'Days', 'value': 'day'},
    {'label': 'Hours', 'value': 'hour'},
    {'label': 'Minutes', 'value': 'minute'},
    {'label': 'Seconds', 'value': 'second'},
]
errorBars_options = [
    {'label': 'Show as Error Bar', 'value': 'bar'},
    {'label': 'Show as Separate Data', 'value': 'separate'},
    {'label': 'Hide', 'value': 'hide'}
]

plotType_options = [
    {'label': 'Marker', 'value': 'markers'},
    {'label': 'Line', 'value': 'lines'},
    {'label': 'Marker+Line', 'value': 'lines+markers'}
]

navbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.NavbarBrand("JWST precision timing",
                            href="javascript:location.reload()"),
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(
                dbc.Nav(
                    [
                        dbc.NavItem(dbc.NavLink(
                            "2D Plot", href="/", id="2d-plot-link")),
                        dbc.NavItem(dbc.NavLink(
                            "Matrix", href="/matrix", id="matrix-link")),
                        dbc.NavItem(dbc.NavLink("Signal-to-noise",
                                    href="/noise", id="noise-link"))
                    ],
                    className="ml-auto",
                    navbar=True,
                ),
                id="navbar-collapse",
                navbar=True,
            ),
            dbc.NavItem(
                dbc.NavLink("Settings", href="#",
                            id="settings-link", style={"color": "white"})
            ),
        ],
        fluid=True
    ),
    color="primary",
    dark=True,
)


modal = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader("Settings"),
                dbc.ModalBody([
                    html.Div(id="plotTypeControl", style={'display': 'none'}, children=[
                        html.P("Plot Type:",
                               style={'margin-top': '8px',
                                      'margin-bottom': '4px'},
                               className='font-weight-bold'),
                        html.Form([
                            html.Div([
                                dcc.Dropdown(
                                    id='plotType', options=plotType_options, value='markers'),
                            ])
                        ])]),
                    # html.Hr(),
                    html.P('Legend Font Size',
                           style={'margin-top': '8px', 'margin-bottom': '4px'},
                           className='font-weight-bold'),
                    dcc.Slider(
                        id='legendFontSize',
                        min=5, max=30, step=1,
                        value=12, marks={i: str(i) for i in range(5, 31, 5)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    html.P('Label Font Size',
                           style={'margin-top': '8px', 'margin-bottom': '4px'},
                           className='font-weight-bold'),
                    dcc.Slider(
                        id='labelFontSize',
                        min=5, max=30, step=1,
                        value=14, marks={i: str(i) for i in range(5, 31, 5)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    html.P('Tooltip Font Size',
                           style={'margin-top': '8px', 'margin-bottom': '4px'},
                           className='font-weight-bold'),
                    dcc.Slider(
                        id='tooltipFontSize',
                        min=5, max=30, step=1,
                        value=12, marks={i: str(i) for i in range(5, 31, 5)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    html.P('Thumnails Size',
                           style={'margin-top': '8px', 'margin-bottom': '4px'},
                           className='font-weight-bold'),
                    dcc.Slider(
                        id='thumnailsSize',
                        min=50, max=150, step=1,
                        value=80, marks={i: str(i) for i in range(50, 150, 10)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),]
                ),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close", className="ml-auto")
                ),
            ],
            id="modal",
            centered=True,
        )
    ]
)

sidebar = html.Div(
    [
        dbc.Row(
            [
                html.Div([
                    html.P('Please select data type',
                           style={'margin-top': '8px', 'margin-bottom': '4px'},
                           className='font-weight-bold'),
                    dcc.Dropdown(id='dataType', multi=False, value='average',
                                 options=data_type_options,
                                 ),
                    html.Hr(),
                    html.P('Please select data to plot',
                           style={'margin-top': '16px',
                                  'margin-bottom': '4px'},
                           className='font-weight-bold'),
                    dcc.Dropdown(id='dataSelection', multi=True,
                                 value=[],
                                 options=dataList,
                                 ),
                    html.Div(id='dropdown-message', style={'color': 'red'}),
                    html.Hr(),
                    html.Div(id='avgGroup', style={'display': 'none'}, children=[
                        html.P("Configure Average Data",
                                title="Adjust the parameters below to set up averaging calculations.",
                               style={'margin-top': '8px',
                                      'margin-bottom': '4px'},
                               className='font-weight-bold'),
                        html.Form([
                            html.Div(id='avgGroup1', style={'display': 'none'}, children=[
                                html.Label(
                                    "Number of bins", title="Number of bins determines the number of intervals in the data range."),
                                html.Br(),
                                dbc.Row(
                                    children=[
                                        dbc.Col(
                                            dcc.Slider(5, 1000, 1,
                                                       value=100, marks=None,
                                                       id='noOfBins', tooltip={"placement": "bottom", "always_visible": True}),
                                            width=8),
                                        dbc.Col(
                                            dbc.Input(
                                                id="noOfBinsValue",
                                                type="number", min=5, max=1000, step=1, ), width=4),
                                    ]
                                )
                            ]),
                            html.Div(id='avgGroup2', style={'display': 'none'}, children=[
                                html.Label(
                                    "Rebinning Factor", title="Specify the number of data points to be grouped together and used for calculating the average."),
                                html.Br(),
                                dbc.Row(
                                    children=[
                                        dbc.Col(dcc.Slider(1, 1000, 1,
                                                           value=100, marks=None,
                                                           id='noOfDataPoint', tooltip={"placement": "bottom", "always_visible": True}), width=8),
                                        dbc.Col(dbc.Input(
                                            id="noOfDataPointValue",
                                            type="number", min=1, max=1000, step=1,
                                        ), width=4),
                                    ]
                                )
                            ])
                        ]),
                        html.Hr(),
                    ]),
                    html.Div(id="xAxisControl", style={'display': 'none'}, children=[
                        html.P("X-axis:",
                               style={'margin-top': '8px',
                                      'margin-bottom': '4px'},
                               className='font-weight-bold'),
                        html.Form([
                            html.Div([
                                dcc.Dropdown(
                                    id='xAxis', options=xAxis_options, value='phase'),
                            ])
                        ])
                    ]),
                    html.Div(id="errorControl", style={'display': 'none'}, children=[
                        html.P("Error Bars:",
                               style={
                                   'margin-top': '8px', 'margin-bottom': '4px'},
                               className='font-weight-bold'),
                        html.Form([
                            html.Div([
                                dcc.Dropdown(
                                    id='errorBars', options=errorBars_options, value='hide'),
                            ])
                        ])]),
                ]
                )
            ],
        )
    ]
)

content = html.Div(id="page-content", children=[
    html.P(id='plot-title', className='font-weight-bold'),
    dbc.Row(id="2d_plot",
            children=[
                dbc.Col(
                    [
                        html.Div([
                            # html.P(id='plot-title',
                            #        className='font-weight-bold'),
                            dcc.Store(id='annotations-store', data=[]),
                            html.Div(id="output-div"),
                            dcc.Graph(id='plot-chart',
                                      className='bg-light', clear_on_unhover=True)]),
                            dcc.Tooltip(id="graph-tooltip"),
                    ])
            ],
            style={'margin': '8px', 'display': 'none'}),
    dbc.Row(id="imageContent",
            children=[
                dbc.Col(
                    [
                        dcc.Store(id='value-store', data=0),
                        html.Div(id='image-container',
                                 style={'display': 'flex', 'flexWrap': 'wrap', 'margin-top': '20px'}),
                        dbc.Modal(
                            [
                                dbc.ModalHeader(
                                    dbc.ModalTitle("Image Details")),
                                dbc.ModalBody(
                                    [
                                        html.Img(id='modal-image',
                                                 style={'width': '100%'}),
                                        # New div for displaying details
                                        html.Div(id='modal-details')
                                    ]
                                ),
                                dbc.ModalFooter(
                                    dbc.Button("Close", id='close-modal',
                                               className='ms-auto', n_clicks=0)
                                ),
                            ],
                            id='image-modal',
                            is_open=False,
                        )
                    ])
            ],
            style={'margin': '8px', 'display': 'none'}),
    dbc.Row(id="matrix_plot",
            children=[
                # dbc.Col(
                #     [
                #         html.P(id='plot-title', className='font-weight-bold'),
                #     ], width=12),
                dbc.Col(
                    [
                        html.Div([
                            dcc.Graph(id='scatter-matrix-sw',
                                      className='bg-light')])
                    ], width=6),
                dbc.Col(
                    [
                        html.Div([
                            dcc.Graph(id='scatter-matrix-lw',
                                      className='bg-light')])
                    ], width=6)
            ],
            style={'margin': '8px', 'display': 'none'})
])

color_list = [
    "rgb(0, 0, 255)",    # Blue
    "rgb(255, 0, 0)",    # Red
    "rgb(0, 255, 0)",    # Green
    "rgb(255, 165, 0)",  # Orange
    "rgb(128, 0, 128)",  # Purple
    "rgb(0, 255, 255)",  # Cyan
    "rgb(255, 0, 255)",  # Magenta
    "rgb(255, 192, 203)",  # Pink
    "rgb(0, 0, 0)",      # Black
    "rgb(128, 128, 128)"  # Gray
]


def weightedAvg(element, error):
    # Convert to NumPy array with float dtype
    elements = np.array(element, dtype=float)
    # Convert to NumPy array with float dtype
    errors = np.array(error, dtype=float)

    # elements = np.array(element)
    # errors = np.array(error)

    # Check for NaN values in elements or errors
    if np.any(np.isnan(elements)) or np.any(np.isnan(errors)):
        return np.nan, np.nan

    variance = errors * errors
    weights = 1.0 / variance

    sum = 0.0
    sumW = 0.0

    for (e, w) in zip(elements, weights):
        sum += e * w
        sumW += w

    avg = sum / sumW  # the weighted mean
    avgErr = 1 / math.sqrt(sumW)  # standard error of the weighted mean
    # print("Input: ",element, error)
    # print("Output: ",avg, avgErr)
    return avg, avgErr


def normalAvg(element, error):
    # Convert to NumPy array with float dtype
    elements = np.array(element, dtype=float)
    # Convert to NumPy array with float dtype
    errors = np.array(error, dtype=float)
    # Check for NaN values in elements or errors
    if np.any(np.isnan(elements)) or np.any(np.isnan(errors)):
        return np.nan, np.nan
    avg = np.average(elements)
    avgErr = np.sqrt(np.sum(errors**2)) / len(errors)

    return avg, avgErr


def create_trace(x_value, y_value, e_value, customdata, hoverinfo, hovertemplate, plotType, errorBars, name, wave_type, color_index):
    traces = []
    color = color_list[color_index % len(color_list)]
    common_props = {
        'x': x_value,
        'y': y_value,
        'mode': plotType,
        'opacity': 0.8,
        'name': f"{name} ({len(y_value)})",
        'legendgroup': wave_type.lower(),
        'legendgrouptitle_text': f"{wave_type} Group",
        'marker': {'color': color},
        'line': {'color': color},
        'customdata': customdata,
        'hoverinfo': hoverinfo,
        'hovertemplate': hovertemplate
    }
    if errorBars == 'bar':
        trace = go.Scattergl(
            **common_props,
            error_y=dict(type='data', array=e_value)
        )
        traces.append(trace)
    elif errorBars == 'hide':
        trace = go.Scattergl(**common_props)
        traces.append(trace)
    elif errorBars == 'separate':
        traces.append(go.Scattergl(**common_props))
        traces.append(go.Scattergl(
            x=x_value,
            y=np.array(y_value) + np.array(e_value),
            mode=plotType,
            opacity=0.8,
            name=f'{name} Error (+) ({len(y_value)})',
            legendgroup=wave_type.lower(),
            legendgrouptitle_text=f"{wave_type} Group",
            marker={'color': color},
            line={'color': color}
        ))
        traces.append(go.Scattergl(
            x=x_value,
            y=np.array(y_value) - np.array(e_value),
            mode=plotType,
            opacity=0.8,
            name=f'{name} Error (-) ({len(y_value)})',
            legendgroup=wave_type.lower(),
            legendgrouptitle_text=f"{wave_type} Group",
            marker={'color': color},
            line={'color': color}
        ))
    return traces


def update_trace(wave_type, dataType, dataSelection, noOfBins, xAxis, errorBars, plotType, noOfDataPoint, pathname):
    traces = []
    color_index = 0
    if pathname == "/noise":
        errorBars = 'hide'
    for label in dataSelection:
        epoch, r_in, r_out = label.split('_')
        epoch = str(epoch)
        r_in = int(r_in)
        r_out = int(r_out)
        # if f"{epoch}_{wave_type.lower()}_{r_in}_{r_out}" not in rawdata:
        #     rawdata[f"{epoch}_{wave_type.lower()}_{r_in}_{r_out}"] = get_data("jwst_rawdata","ZTF_J1539",f"{epoch}_{wave_type.lower()}_{r_in}_{r_out}")
        # d = rawdata[f"{epoch}_{wave_type.lower()}_{r_in}_{r_out}"]
        d = get_data("jwst_rawdata", rawdata, data_for_df,
                     "ZTF_J1539", isDB, epoch, wave_type, r_in, r_out)
        # d = get_data("jwst_rawdata","ZTF_J1539",f"{epoch}_{wave_type.lower()}_{r_in}_{r_out}")
        # d = rawdata[f"{epoch}_{wave_type.lower()}_{r_in}_{r_out}"]
        # d = rawdata[epoch][wave_type.lower()][r_in][r_out]
        time = Time(np.array(d['time']), format="mjd", scale="tdb")
        time_mjd = np.array(d['time_mjd'])
        time_second = np.array(d['time_second'])
        time_minute = np.array(d['time_minute'])
        time_hour = np.array(d['time_hour'])
        time_day = np.array(d['time_day'])
        time_day = np.array(d['time_day'])
        phase_values = np.array(d['phase_values'])
        psf_flux_time = np.array(d['psf_flux_time'])
        psf_flux_unc_time = np.array(d['psf_flux_unc_time'])
        frame = np.array(d['frame']).astype(int)
        customdata_time = np.array(d['customdata_time'])

        phase_values_phase = np.array(d['phase_values_phase'])
        time_mjd_phase = np.array(d['time_mjd_phase'])
        psf_flux_phase = np.array(d['psf_flux_phase'])
        psf_flux_unc_phase = np.array(d['psf_flux_unc_phase'])
        frame_phase = np.array(d['frame_phase']).astype(int)
        customdata_phase = np.array(d['customdata_phase'])
        # print(customdata_phase)
        time_arrays = {
            'mjd': time_mjd,
            'time': time_mjd,
            'second': time_second,
            'minute': time_minute,
            'hour': time_hour,
            'day': time_day
        }
        noOfChunks = len(psf_flux_time) // noOfDataPoint
        bin_edges = np.linspace(0, 2, noOfBins + 1)
        name = f'{epoch}.{wave_type}.{r_in}.{r_out}'

        if dataType == 'average':
            hovertemplate = ('Y-Axis: %{y}<br>'
                             'Phase: %{customdata.phase:.3f}<extra></extra>'
                             )
            hoverinfo = "all"
            x_value = []
            y_value = []
            e_value = []
            # # ===================== For checking
            # x_value2 = []
            # y_value2 = []
            # e_value2 = []
            # # ==================================
            customdata = []
            if xAxis == 'phase':
                bin_indices = np.digitize(phase_values_phase, bin_edges) - 1
                for i in range(noOfBins):
                    bin_mask = (bin_indices == i)
                    if np.any(bin_mask):
                        x_value.append((bin_edges[i] + bin_edges[i+1]) / 2)
                        avg, avgErr = weightedAvg(np.array(psf_flux_phase)[
                                                  bin_mask], np.array(psf_flux_unc_phase)[bin_mask])
                        y_value.append(avg)
                        e_value.append(avgErr)
                        customdata.append({
                            'mjd': time_mjd_phase[bin_mask].mean(),
                            'time': Time(time_mjd_phase[bin_mask].mean(), format="mjd", scale="tdb").datetime,
                            'phase': (bin_edges[i] + bin_edges[i+1]) / 2,
                            'datatype': "average"
                        })
                        # # ===================== For checking
                        # x_value2.append((bin_edges[i] + bin_edges[i+1]) / 2)
                        # avg, avgErr = normalAvg(np.array(psf_flux_phase)[bin_mask], np.array(psf_flux_unc_phase)[bin_mask])
                        # y_value2.append(avg)
                        # e_value2.append(avgErr)
                        # # ==================================

            else:
                avg_time, remaining_time = [], []
                # avg_time, remaining_time, y_value, e_value = [], [], [], []
                # customdata = []
                for i in range(noOfChunks):
                    chunk_flux_time = psf_flux_time[i *
                                                    noOfDataPoint: (i + 1) * noOfDataPoint]
                    chunk_flux_unc_time = psf_flux_unc_time[i *
                                                            noOfDataPoint: (i + 1) * noOfDataPoint]
                    avg, avgErr = weightedAvg(
                        chunk_flux_time, chunk_flux_unc_time)
                    y_value.append(avg)
                    e_value.append(avgErr)
                    customdata.append({
                        'mjd': time_mjd[i * noOfDataPoint: (i + 1) * noOfDataPoint].mean(),
                        'time': Time(time_mjd[i * noOfDataPoint: (i + 1) * noOfDataPoint].mean(), format="mjd", scale="tdb").datetime,
                        'phase': phase_values[i * noOfDataPoint: (i + 1) * noOfDataPoint].mean(),
                        'datatype': "average"
                    })

                    # # ===================== For checking
                    # avg, avgErr = normalAvg(chunk_flux_time, chunk_flux_unc_time)
                    # y_value2.append(avg)
                    # e_value2.append(avgErr)
                    # # ==================================
                remaining_start_idx = noOfChunks * noOfDataPoint
                remaining_fluxes = psf_flux_time[remaining_start_idx:]
                remaining_flux_uncs = psf_flux_unc_time[remaining_start_idx:]
                if xAxis in time_arrays:
                    avg_time = [np.mean(
                        time_arrays[xAxis][i * noOfDataPoint: (i + 1) * noOfDataPoint]) for i in range(noOfChunks)]
                    remaining_time = time_arrays[xAxis][remaining_start_idx:]
                else:
                    raise ValueError(f"Unknown xAxis value: {xAxis}")
                if len(remaining_time) > 0:
                    avg_time.append(np.mean(remaining_time))
                    avg, avgErr = weightedAvg(
                        remaining_fluxes, remaining_flux_uncs)
                    y_value.append(avg)
                    e_value.append(avgErr)
                    customdata.append({
                        'mjd': time_mjd[remaining_start_idx:].mean(),
                        'time': Time(time_mjd[remaining_start_idx:].mean(), format="mjd", scale="tdb").datetime,
                        'phase': phase_values[remaining_start_idx:].mean(),
                        'datatype': "average"
                    })
                    # # ===================== For checking
                    # avg, avgErr = normalAvg(remaining_fluxes, remaining_flux_uncs)
                    # y_value2.append(avg)
                    # e_value2.append(avgErr)
                    # # ==================================
                if xAxis == 'time':
                    x_value = Time(avg_time, format="mjd",
                                   scale="tdb").datetime
                else:
                    x_value = avg_time
                # # ===================== For checking
                # x_value2 = x_value
                # # ==================================
            if pathname == "/noise":
                y_temp = [y/e for y, e in zip(y_value, e_value)]
                y_value = y_temp
                # # ===================== For checking
                # y_temp2 = [y/e for y, e in zip(y_value2, e_value2)]
                # y_value2 = y_temp2
                # # ==================================
            traces.extend(create_trace(x_value, y_value, e_value, customdata, hoverinfo, hovertemplate,
                          plotType, errorBars, name, wave_type, color_index))
            # # ===================== For checking
            # traces.extend(create_trace(x_value2, y_value2, e_value2, customdata, hovertemplate,
            #               plotType, errorBars, name+" normal avg ", wave_type, color_index+1))
            # # ===================================
        elif dataType == 'raw':
            # hovertemplate = ('Y-Axis: %{y}<br>'
            #                  'MJD: %{customdata.mjd:.5f}<br>'
            #                  'Time:  %{customdata.time}<br>'
            #                  'Phase: %{customdata.phase:.3f}<extra></extra>'
            #                  )
            hovertemplate = None
            hoverinfo = "none"
            x_value = phase_values_phase
            y_value = psf_flux_phase
            e_value = psf_flux_unc_phase
            customdata = customdata_phase
            if xAxis != 'phase':
                y_value = psf_flux_time
                e_value = psf_flux_unc_time
                customdata = customdata_time
                if xAxis in time_arrays:
                    x_value = time_arrays[xAxis]
                else:
                    raise ValueError(f"Unknown xAxis value: {xAxis}")
                if xAxis == 'time':
                    x_value = Time(x_value, format="mjd", scale="tdb").datetime
            if pathname == "/noise":
                y_temp = [y/e for y, e in zip(y_value, e_value)]
                y_value = y_temp
            traces.extend(create_trace(x_value, y_value, e_value, customdata, hoverinfo, hovertemplate,
                          plotType, errorBars, name, wave_type, color_index))
        color_index = color_index+1
    return traces


def update_df(wave_type, dataType, dataSelection, plotType, noOfDataPoint):
    data = {}
    max_length = 0
    for label in dataSelection:
        epoch, r_in, r_out = label.split('_')
        epoch = str(epoch)
        r_in = int(r_in)
        r_out = int(r_out)
        # if f"{epoch}_{wave_type.lower()}_{r_in}_{r_out}" not in data_for_df:
        #     data_for_df[f"{epoch}_{wave_type.lower()}_{r_in}_{r_out}"] = get_data("df","ZTF_J1539",f"{epoch}_{wave_type.lower()}_{r_in}_{r_out}")
        # d = data_for_df[f"{epoch}_{wave_type.lower()}_{r_in}_{r_out}"]
        # d = data_for_df[epoch][wave_type.lower()][r_in][r_out]
        d = get_data("df", rawdata, data_for_df, "ZTF_J1539",
                     isDB, epoch, wave_type, r_in, r_out)
        psf_flux_time = np.array(d['psf_flux_time'])
        psf_flux_unc_time = np.array(d['psf_flux_unc_time'])
        time_mjd = np.array(d['time_mjd'])

        noOfChunks = len(psf_flux_time) // noOfDataPoint
        name = f'{wave_type}.{r_in}.{r_out}'
        x_value = []
        y_value = []
        if dataType == 'average':
            avg_time, remaining_time, y_value, e_value = [], [], [], []
            for i in range(noOfChunks):
                chunk_flux_time = psf_flux_time[i *
                                                noOfDataPoint: (i + 1) * noOfDataPoint]
                chunk_flux_unc_time = psf_flux_unc_time[i *
                                                        noOfDataPoint: (i + 1) * noOfDataPoint]
                avg, avgErr = weightedAvg(chunk_flux_time, chunk_flux_unc_time)
                y_value.append(avg)
                e_value.append(avgErr)
            remaining_start_idx = noOfChunks * noOfDataPoint
            remaining_fluxes = psf_flux_time[remaining_start_idx:]
            remaining_flux_uncs = psf_flux_unc_time[remaining_start_idx:]
            avg_time = [np.mean(
                time_mjd[i * noOfDataPoint: (i + 1) * noOfDataPoint]) for i in range(noOfChunks)]
            remaining_time = time_mjd[remaining_start_idx:]
            if len(remaining_time) > 0:
                avg_time.append(np.mean(remaining_time))
                avg, avgErr = weightedAvg(
                    remaining_fluxes, remaining_flux_uncs)
                y_value.append(avg)
                e_value.append(avgErr)
            x_value = avg_time
        elif dataType == 'raw':
            x_value = time_mjd
            y_value = psf_flux_time
        data[name] = y_value
        max_length = max(max_length, len(y_value))
    df = pd.DataFrame(data=data)
    return df


def get_epoch(text):
    """Extract epoch from the file name using regex."""
    match = re.search(r'epoch(\d+)\_', text)
    if match:
        return match.group(1)
    return None
