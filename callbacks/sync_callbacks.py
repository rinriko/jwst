from dash.dependencies import Input, Output, State
import dash
def register_sync_callbacks(app):
    @app.callback(
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
