import dash
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from components import data_type_options, get_epoch, xAxis_options, color_list, sidebar, navbar, content, update_trace, update_df, modal

def register_matrix_callbacks(app):
    @app.callback(
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
