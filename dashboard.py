from dash import Dash, dcc, html


def init_dashboard(server):
    """Create a Plotly Dash dashboard."""
    dash_app = Dash(
        server=server,
        routes_pathname_prefix='/dashapp/',
        #external_stylesheets=['/static/dist/css/styles.css',]
    )

    # Create Dash Layout
    dash_app.layout = html.Div(id='dash-container')

    # Initialize callbacks after our app is loaded
    init_callbacks(dash_app)    

    return dash_app.server


def init_callbacks(dash_app):
    @dash_app.callback()
    def update_graph(rows):
        # Callback logic
        pass