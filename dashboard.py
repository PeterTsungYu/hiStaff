from distutils.log import debug
from datetime import date
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
        # content will be rendered in this element
        html.Div(id='page-content', children=[])
    ])

    # Initialize callbacks after our app is loaded
    init_callbacks()    

    return dash_app.server


def init_callbacks():

    index_page = html.Div([
        dcc.Link('Navigate to "CHECK IN TABLE"', href=f'{url_prefix}checkin'),
        html.Br(),
        dcc.Link('Navigate to "CHECK OUT TABLE"', href=f'{url_prefix}checkout'),
    ])

    check_in_layout = html.Div([
        html.H1('CHECK IN TABLE'),
        dcc.Dropdown(['LA', 'NYC', 'MTL'], 'LA', id='page-1-dropdown'),
        html.Div(id='check-in-table'),
        html.Br(),
        dcc.Link('Navigate to "CHECK OUT TABLE"', href=f'{url_prefix}checkout'),
        html.Br(),
        dcc.Link('Go back to home', href=f'{url_prefix}'),
    ])
    
    check_out_layout = html.Div([
        html.H1('CHECK OUT TABLE'),
        dcc.Dropdown(['a', 'b', 'c'], 'LA', id='page-2-dropdown'),
        html.Div(id='check-out-table'),
        html.Br(),
        dcc.Link('Navigate to "CHECK IN TABLE"', href=f'{url_prefix}checkin'),
        html.Br(),
        dcc.Link('Go back to home', href=f'{url_prefix}'),
    ])
    
    @callback(
        Output('check-in-table', 'children'),
        [Input('page-1-dropdown', 'value')]
        )
    def page_1_dropdown(value):
        return f'You have selected {value}'
    
    @callback(
        Output('check-out-table', 'children'),
        [Input('page-2-dropdown', 'value')]
        )
    def page_2_radios(value):
        return f'You have selected {value}'
    
    # Update the index
    @callback(
        Output('page-content', 'children'),
        [Input('url', 'pathname')]
        )
    def display_page(pathname):
        if pathname == f'{url_prefix}checkin':
            return check_in_layout
        elif pathname == f'{url_prefix}checkout':
            return check_out_layout
        else:
            return index_page
        # You could also return a 404 "URL not found" page here