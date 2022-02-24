# library
from distutils.log import debug
from dash import Dash, dcc, html, callback, Input, Output
from urllib.parse import urlparse, unquote, parse_qsl

# custom
import db
import config

url_prefix = config.dash_prefix

def init_dashboard(server):
    """Create a Plotly Dash dashboard."""
    dash_app = Dash(
        server=server,
        #requests_pathname_prefix='/hiStaff_dashapp/',
        routes_pathname_prefix=url_prefix+'/',
        external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'],
    )

    url = dcc.Location(id='url', refresh=False)
    # Create Dash Layout
    dash_app.layout = html.Div(children=[
        # represents the browser address bar and doesn't render anything
        url,
        # content will be rendered in this element
        html.Div(id='page-content', children=[])
    ])

    # Initialize callbacks after our app is loaded
    init_callbacks()    

    return dash_app.server


def init_callbacks():

    check_h1 = html.H1(id='check-h1')
    check_table = html.Div(id='check-table')
    check_link = dcc.Link(id='check-link', href=f'{url_prefix}/')
    home_link = dcc.Link(id='home-link', href=f'{url_prefix}/')
    index_dropdown = dcc.Dropdown(['checkin', 'checkout'], 'checkin', id='index-dropdown')
    index_link = dcc.Link(id='index-link', href='')
    
    index_page = [html.Div([
        index_dropdown,
        html.Br(),
        index_link,
    ])]

    check_layout = [html.Div([
        check_h1,
        check_table,
        html.Br(),
        check_link,
        html.Br(),
        home_link,
    ])]

    @callback(
        [
            Output('index-link', 'children'),
            Output('index-link', 'href'),
            ],
        [
            Input('index-dropdown', 'value'),
            Input('url', 'search'),
            ]
        )
    def index_linking(value, search):
        staff = dict(parse_qsl(unquote(search))).get('?staff')
        children = staff + '/' + value
        href = url_prefix + '/' + value + search 
        config.logging.debug(href)
        return children, href
    
    # Update the index
    @callback(
        [
            Output('page-content', 'children'),
            ],
        [
            Input('url', 'pathname'), 
            Input('url', 'search'),
            ]
        )
    def display_page(pathname, search):
        config.logging.debug([pathname, search])
        check_type = pathname.split(f'{url_prefix}')[-1]
        if 'checkin' in check_type:
            other_type = '/checkout'
        else:
            other_type = '/checkin'
        staff = dict(parse_qsl(unquote(search))).get('?staff')
        config.logging.debug([check_type, staff])
        check_h1.children = staff + check_type
        check_link.children = staff + other_type
        check_link.href = url_prefix + other_type + search
        home_link.children = staff + '/Sweet Home'
        home_link.href = url_prefix + search

        
        if f'{url_prefix}/check' in pathname:
            return check_layout
        else:
            return index_page
        # You could also return a 404 "URL not found" page here