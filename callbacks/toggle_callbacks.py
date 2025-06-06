from dash.dependencies import Input, Output, State

def register_toggle_callbacks(app):
    # sidebar
    @app.callback(
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


    @app.callback(
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

    @app.callback(
        Output("modal", "is_open"),
        [Input("settings-link", "n_clicks"), Input("close", "n_clicks")],
        [State("modal", "is_open")],
    )
    def toggle_modal(n1, n2, is_open):
        if n1 or n2:
            return not is_open
        return is_open


    @app.callback(
        [Output("2d-plot-link", "active"),
        Output("matrix-link", "active"),
        Output("noise-link", "active")],
        [Input("url", "pathname")]
    )
    def toggle_active_links(pathname):
        return [pathname == "/", pathname == "/matrix", pathname == "/noise"]


    @app.callback(
        Output("navbar-collapse", "is_open"),
        [Input("navbar-toggler", "n_clicks")],
        [State("navbar-collapse", "is_open")],
    )
    def toggle_navbar_collapse(n, is_open):
        if n:
            return not is_open
        return is_open


