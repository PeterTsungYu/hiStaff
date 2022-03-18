# library
from distutils.log import debug
from dash import Dash, dcc, html, callback, Input, Output, dash_table, State
from dash.dash_table import DataTable
from urllib.parse import urlparse, unquote, parse_qsl
import dash_bootstrap_components as dbc
from datetime import datetime, date
import pandas as pd
import json
import numpy as np

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

    url = dcc.Location(id='url', refresh=True)
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

    now_date = datetime.now().date()

    # dash components
    check_h1 = html.H1(id='check_h1')
    check_datepicker = dcc.DatePickerRange(
                        id='check_datepicker',
                        min_date_allowed=date(1992, 1, 25),
                        max_date_allowed=date(2092, 1, 25),
                        initial_visible_month=now_date,
                        start_date=(now_date  - pd.offsets.MonthBegin(1)).date(),
                        end_date=now_date
        )
    check_datatable_div = html.Div(id='check_datatable_div')
    sum_string = html.Div(id='sum_string')
    change_string = html.Div(id='change_string')
    check_button = dcc.ConfirmDialogProvider(
        children=html.Button('Edit',),
        id='check_button',
        message='Ready to submit your change to your working time data. Pls double make sure it.'
        )
    check_link = dcc.Link(id='check_link', href=f'{url_prefix}/')
    home_link = dcc.Link(id='home_link', href=f'{url_prefix}/')
    index_dropdown = dcc.Dropdown(['checkin', 'checkout'], 'checkin', id='index_dropdown')
    index_link = dcc.Link(id='index_link', href='')
    def check_table(check_df):
        datatable = DataTable(
                            id='check_datatable',
                            columns=[{"name": i, "id": i, "deletable": False, "selectable": False, "editable":True} if i in ['checkin', 'checkout'] else {"name": i, "id": i, "deletable": False, "selectable": False, "editable":False} for i in check_df.columns],
                            data=check_df.to_dict('records'),
                            editable=True,
                            filter_action="native",
                            sort_action="native",
                            sort_mode="multi",
                            column_selectable=False,
                            row_selectable=False,
                            row_deletable=False,
                            selected_columns=[],
                            selected_rows=[],
                            page_action="native",
                            page_current= 0,
                            page_size= 10,
                            style_cell={                # ensure adequate header width when text is shorter than cell's text
                                'minWidth': 65, 'maxWidth': 95, 'width': 95,
                                'overflow': 'hidden',
                                'textOverflow': 'ellipsis',
                                'maxWidth': 0,
                            },
                            style_cell_conditional=[    # align text columns to left. By default they are aligned to right
                                {
                                    'if': {'column_id': c},
                                    'textAlign': 'left'
                                } for c in ['date', 'checkin', 'checkout']
                            ],
                            style_data={                # overflow cells' content into multiple lines
                                'whiteSpace': 'normal',
                                'height': 30
                            },
                            tooltip_data=[
                                {
                                    column: {'value': f'Edit with following format: "HH:MM:SS"', 'type': 'markdown'}
                                    if column in ['checkin', 'checkout']
                                    else f"{value} [hr]"
                                    for column, value in row.items()
                                    
                                } 
                                for row in check_df.to_dict('records')
                            ],
                            tooltip_delay=0,
                            tooltip_duration=None
                        )
        return datatable
    
    # dcc store
    personal_data_store = dcc.Store(id='personal_data_store')
    previous_check_store = dcc.Store(id='previous_check_store')
    agg_check_store = dcc.Store(id='agg_check_store')
    check_changes_store = dcc.Store(id='check_changes_store')

    
    # dash layouts
    index_page = [html.Div([
        index_dropdown,
        html.Br(),
        index_link,
        personal_data_store,
    ])]

    check_layout = [html.Div([
        check_h1,
        check_datepicker,
        check_datatable_div,
        sum_string,
        change_string,
        check_button,
        html.Br(),
        check_link,
        html.Br(),
        home_link,
        personal_data_store,
        previous_check_store,
        agg_check_store,
        check_changes_store,
    ])]


    # datepicker for check_table
    @callback(
        [
            Output('check_datatable_div', 'children'),
            Output('previous_check_store', 'data'),
            Output('agg_check_store', 'data'),
            Output('sum_string', 'children'),
            ],
        [
            Input('check_datepicker', 'start_date'),
            Input('check_datepicker', 'end_date'),
            Input('url', 'search'),
            ],
        )
    def datepicker_check_table(start_date, end_date, search):
        print(f'{search} from datepicker_check_table')
        staff = dict(parse_qsl(unquote(search))).get('?staff')
        print(start_date)
        print(end_date)
        check_df = db.table_generator(start_date, end_date, staff).check_dataframe()
        agg_check = check_df['aggregation[hr]'].iloc[-1]
        return [
            check_table(check_df), 
            check_df.to_json(orient='split', date_format='iso'),
            agg_check,
            f"This month till now, u've worked for {agg_check} [hr].",
        ]


    # update the table         
    @callback(
    [
        Output('url', 'refresh'),
        Output('url', 'href'),
        Output('change_string', 'children'), 
        ],
    Input('check_button', 'submit_n_clicks'),
    [
        State('url', 'search'),
        State('url', 'pathname'),
        State('check_datepicker', 'start_date'),
        State('check_datepicker', 'end_date'),
        State('check_button', 'submit_n_clicks_timestamp'),
        State('check_datatable', 'data'),
        State('previous_check_store', 'data'),
        ],
    prevent_initial_call=False,
    )
    def update_check_data(submit_n_clicks, search, pathname, start_date, end_date, submit_n_clicks_timestamp, data, data_previous):
        #print(data) # list of dictionaries of str or None
        #print(json.loads(data_previous))
        staff_name = dict(parse_qsl(unquote(search))).get('?staff')
        if (data != None) and (data_previous) != None:
            df = pd.DataFrame(data=data)
            df_previous = pd.read_json(data_previous, orient='split')
            print(df)
            print(df_previous)
            mask = df.ne(df_previous)
            df_diff = df[mask]
            print(df_diff)
            changes = {}
            count = 0
            for index, row in df_diff.iterrows():
                for col, value in row.items():
                    if col not in ('checkin', 'checkout'):
                        continue
                    if str(value).strip() not in ('None', 'nan'):
                        date = df['date'][index].split(',')[0]
                        if value != '':
                            print(value, date)
                            current_time = value
                            current_datetime = date + '/' + current_time
                        else:
                            current_datetime = None
                        
                        if 'checkin' in col:
                            pre_time = df_previous['checkin'][index]
                        elif 'checkout' in col:
                            pre_time = df_previous['checkout'][index]
                        
                        if (pre_time != None) and (pre_time != ''):
                            pre_datetime = date + '/' + pre_time
                        else:
                            pre_datetime = None
                        # include the other table ... to compare the other for time diff
                        changes[f'{count}'] = {'col':col, 'previous':pre_datetime, 'current':current_datetime}
                        count += 1

            for key, value in changes.items():
                print(key, value)
                col = f"{value['col']}"
                if 'checkin' in col:
                    table = db.CheckIn
                elif 'checkout' in col:
                    table = db.CheckOut
                pre = value['previous']
                cur = value['current']
                if (cur == None) and (pre == None):
                    continue
                elif cur == None:
                    try:
                        pre = datetime.strptime(pre, '%m/%d/%Y/%H:%M:%S')
                    except Exception as e:
                        return [
                            False,
                            f"{pathname}{search}",
                            str(e), 
                            ]
                    #delete the row
                    db.db_session.query(table).\
                    filter(table.staff_name == staff_name, table.created_time == pre).\
                    delete()
                elif pre == None:
                    try:
                        cur = datetime.strptime(cur, '%m/%d/%Y/%H:%M:%S')
                    except Exception as e:
                        return [
                            False,
                            f"{pathname}{search}",
                            str(e), 
                            ]
                    # insert a row
                    db.db_session.add(table(staff_name=staff_name, created_time=cur))
                else:
                    try:
                        pre = datetime.strptime(pre, '%m/%d/%Y/%H:%M:%S')
                        cur = datetime.strptime(cur, '%m/%d/%Y/%H:%M:%S')
                        print(pre, cur)
                    except Exception as e:
                        return [
                            False,
                            f"{pathname}{search}",
                            str(e), 
                            ]
                    # update the row
                    db.db_session.query(table).\
                    filter(table.staff_name == staff_name, table.created_time == pre).\
                    update({"created_time": cur})
        db.db_session.commit()
        return [
            True,
            f"{pathname}{search}", #refresh the page
            'Succeed',
            ]


    # update index links
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
        print(f'{search} from index_linking')
        staff = dict(parse_qsl(unquote(search))).get('?staff')
        children = staff + '/' + value
        href = url_prefix + '/' + value + search 
        config.logging.debug(href)
        return children, href
    

    # route to check_layout / index_page
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
        print(f'{search} from display_page')
        config.logging.debug([pathname, search])
        check_type = pathname.split(f'{url_prefix}')[-1]
        if 'checkin' in check_type:
            other_type = '/checkout'
        else:
            other_type = '/checkin'
        
        staff = dict(parse_qsl(unquote(search))).get('?staff')
        personal_data_store.data = {'staff':staff}

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