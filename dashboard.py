from distutils.log import debug
from dash import Dash, dcc, html, callback, Input, Output

url_prefix = '/hiStaff_dashapp/'

def init_dashboard(server):
    """Create a Plotly Dash dashboard."""
    dash_app = Dash(
        server=server,
        #requests_pathname_prefix='/hiStaff_dashapp/',
        routes_pathname_prefix=url_prefix,
        external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'],
    )

    # Create Dash Layout
    dash_app.layout = html.Div(children=[
        # represents the browser address bar and doesn't render anything
        dcc.Location(id='url', refresh=False),

        dcc.Link('Navigate to "CHECK IN TABLE"', href=f'{url_prefix}checkin'),
        html.Br(),
        dcc.Link('Navigate to "CHECK OUT TABLE"', href=f'{url_prefix}checkout'),

        # content will be rendered in this element
        html.Div(id='page-content', children=[])
    ])

    # Initialize callbacks after our app is loaded
    init_callbacks()    

    return dash_app.server


def init_callbacks():
    @callback(
        Output(component_id='page-content', component_property='children'), 
        [Input(component_id='url', component_property='pathname')]
        )
    def display_page(pathname):
        return html.Div([
            html.H3(f'You are on page {pathname}')
        ])