import pandas as pd
from dash.dependencies import Input, Output, State
def register_download_callbacks(app):
    @app.callback(
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

