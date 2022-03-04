# library
from distutils.log import debug
from dash import Dash, dcc, html, callback, Input, Output, dash_table
from urllib.parse import urlparse, unquote, parse_qsl
import dash_bootstrap_components as dbc
from datetime import datetime, date
import pandas as pd

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
        external_stylesheets=[dbc.themes.BOOTSTRAP],
    )

    url = dcc.Location(id='url', refresh=False)
    # Create Dash Layout
    dash_app.layout = html.Div(children=[
        # represents the browser address bar and doesn't render anything
        url,
        # content will be rendered in this element
        html.Div(id='page_content', children=[])
    ])

    # Initialize callbacks after our app is loaded
    init_callbacks()    

    return dash_app.server


def init_callbacks():

    check_h1 = html.H1(id='check_h1')
    check_datepicker = dcc.DatePickerRange(
                        id='check_datepicker',
                        min_date_allowed=date(1992, 1, 25),
                        max_date_allowed=date(2092, 1, 25),
                        initial_visible_month=datetime.now(),
                        start_date=datetime.now(),
                        end_date=datetime.now() - pd.offsets.MonthEnd(1)
        )
    check_date_string = html.Div(id='check_date_string')
    check_datatable =dash_table.DataTable(
                    id='check_datatable',
                    #columns=[{"name": i, "id": i, "deletable": False, "selectable": True} for i in check_df.columns],
                    #data=check_df.to_dict('records'),
                    editable=True,
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    column_selectable="single",
                    row_selectable="multi",
                    row_deletable=True,
                    selected_columns=[],
                    selected_rows=[],
                    page_action="native",
                    page_current= 0,
                    page_size= 10,
                    style_cell={                # ensure adequate header width when text is shorter than cell's text
                        'minWidth': 95, 'maxWidth': 95, 'width': 95
                    },
                    style_cell_conditional=[    # align text columns to left. By default they are aligned to right
                        {
                            'if': {'column_id': c},
                            'textAlign': 'left'
                        } for c in ['date', 'checkin', 'checkout']
                    ],
                    style_data={                # overflow cells' content into multiple lines
                        'whiteSpace': 'normal',
                        'height': 'auto'
                    }
                )
    check_link = dcc.Link(id='check_link', href=f'{url_prefix}/')
    home_link = dcc.Link(id='home_link', href=f'{url_prefix}/')
    index_dropdown = dcc.Dropdown(['checkin', 'checkout'], 'checkin', id='index_dropdown')
    index_link = dcc.Link(id='index_link', href='')

    
    index_page = [html.Div([
        index_dropdown,
        html.Br(),
        index_link,
    ])]

    check_layout = [html.Div([
        check_h1,
        check_datepicker,
        check_datatable,
        check_date_string,
        html.Br(),
        check_link,
        html.Br(),
        home_link,
    ])]


    @callback(
        [
            Output('check_datatable', 'data'),
            ],
        [
            Input('check_datepicker', 'start_date'),
            Input('check_datepicker', 'end_date'),
            Input('url', 'search'),
            ]
        )
    def update_output(start_date, end_date, search):
        staff = dict(parse_qsl(unquote(search))).get('?staff')
        start = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S.%f").date()
        end = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%f").date()
        print(start)
        print(type(start))
        check_df = db.table_generator(start, end, staff).check_table()
        return [
            check_df.to_dict('records'), 
        ]

        

    @callback(
        [
            Output('index_link', 'children'),
            Output('index_link', 'href'),
            ],
        [
            Input('index_dropdown', 'value'),
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
            Output('page_content', 'children'),
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