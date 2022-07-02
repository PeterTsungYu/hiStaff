# library
from distutils.log import debug
from dash import Dash, dcc, html, callback, Input, Output, dash_table, State
from dash.dash_table import DataTable
from dash.exceptions import PreventUpdate
from urllib.parse import urlparse, unquote, parse_qsl
import dash_bootstrap_components as dbc
from datetime import datetime, date, timedelta
from datetimerange import DateTimeRange
import pandas as pd
import json
import numpy as np
import re
import time

# custom
import db
import config
from hicalendar import hiCalendar

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
    
    table_style = {
        'width':'95%', 
        #'background-color': '#0074D9'
    }

    # dash components
    check_h1 = html.H1(id='check_h1')
    check_datepicker = dcc.DatePickerRange(
                        id='check_datepicker',
                        min_date_allowed=date(1992, 1, 25),
                        max_date_allowed=date(2100, 1, 25),
                        initial_visible_month=datetime.now().date(),
                        start_date=(datetime.now().date()  - pd.offsets.MonthBegin(1)).date(),
                        end_date=datetime.now().date()
    )
    check_datatable_div = html.Div(id='check_datatable_div', style=table_style)
    mycheck_datatable_div = html.Div(id='mycheck_datatable_div', style=table_style)
    season_check_datatable_div = html.Div(id='season_check_datatable_div', style=table_style)
    leave_datatable_div = html.Div(id='leave_datatable_div', style=table_style)
    sum_string = html.Div(id='sum_string')
    change_string = html.Div(id='change_string')
    check_button = dcc.ConfirmDialogProvider(
        children=html.Button('Click to edit the table entry',),
        id='check_button',
        message='Ready to submit your change to your working time data. Pls double make sure it.'
        )
    check_link = dcc.Link(id='check_link', href=f'{url_prefix}/')
    home_link = dcc.Link(id='home_link', href=f'{url_prefix}/')
    index_dropdown = dcc.Dropdown(['check', 'Season'], 'check', id='index_dropdown')
    month_dropdown = dcc.Dropdown(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], datetime.now().strftime("%b"), id='month_dropdown', placeholder="Select A Month",)
    year_dropdown = dcc.Dropdown(['2022', '2023', '2024', '2025', '2026'], datetime.now().strftime("%Y"), id='year_dropdown', placeholder="Select A Year",)
    season_dropdown = dcc.Dropdown(['Q1', 'Q2', 'Q3', 'Q4'], 'Q1', id='season_dropdown', placeholder="Select A Quarter",)
    index_link = dcc.Link(id='index_link', href='')

    def check_table(check_df):
        #print(check_df.columns)
        datatable = DataTable(
                            id='check_datatable',
                            columns=[{"name": i, "id": i, "deletable": False, "selectable": False, "editable":True} if i in ['checkin', 'checkout'] else {"name": i, "id": i, "deletable": False, "selectable": False, "editable":False} for i in check_df.columns],
                            data=check_df.to_dict('records'),
                            editable=True,
                            filter_action="native",
                            sort_action="native",
                            sort_mode="multi",
                            page_action="native",
                            page_current= 0,
                            page_size= 10,
                            style_table={'overflowX': 'auto','minWidth': '100%',},
                            style_cell={ 
                                'textAlign': 'center',               # ensure adequate header width when text is shorter than cell's text
                                'minWidth': '180px', 'maxWidth': '180px', 'width': '180px',
                                'whiteSpace': 'normal',
                                'height': '35px',
                                },
                            style_cell_conditional=[    # align text columns to left. By default they are aligned to right
                                {
                                    'if': {'column_id': c},
                                    'textAlign': 'left'
                                } for c in ['date']
                            ],
                            style_data={                # overflow cells' content into multiple lines
                                'whiteSpace': 'normal',
                                'height': 30
                            },
                            style_data_conditional=[
                                {
                                    'if': {
                                        'state': 'active'  # 'active' | 'selected'
                                        },
                                    'backgroundColor': 'rgba(0, 116, 217, 0.3)',
                                    'border': '1px solid rgb(0, 116, 217)'
                                    },
                                {
                                    'if': {
                                        'filter_query': '{date} > ' + f'{(datetime.now().date()-pd.offsets.DateOffset(days=2)).date().strftime("%m/%d/%Y")}',
                                        'column_id': ['checkin', 'checkout']
                                        },
                                    'backgroundColor': '#7FDBFF',
                                    'color': 'white',
                                    'border': '1px solid rgb(0, 116, 217)'
                                    },
                            ],
                            style_header={
                                'backgroundColor': '#0074D9',
                                'color': 'white'
                                },
                            tooltip_data=[
                                {
                                    column: {'value': f'Edit with following format: "HH:MM:SS"', 'type': 'markdown'}
                                    if column in ['checkin', 'checkout']
                                    else f"{value} [hr]"
                                    for column, value in row.items()
                                    
                                } 
                                for row in check_df.to_dict('records')[:]
                            ],
                            tooltip_delay=0,
                            tooltip_duration=None,
                            export_format='xlsx',
                            export_headers='display',
                        )
        return datatable
    
    # leave form objs
    leave_start_datetime_picker = dcc.Input(id='leave_start_datetime_picker', type="datetime-local", step="1")
    leave_card = dbc.Card([
                    dbc.CardHeader("Leave Form"),
                    dbc.CardBody(
                        [
                            html.H5("Leave Type", className="card-title"),
                            html.P(id='leave_unit'),
                            dcc.RadioItems(
                                id="leave_type_radio",
                                options={v['type']:k for (k,v) in db.leaves_type.items()},
                                style={'width':'25%', 'font-size': 20}
                            ),
                            html.Br(),
                            html.H5("Leave Start", className="card-title"),
                            leave_start_datetime_picker,
                            html.Br(),
                            html.Br(),
                            html.H5("Reserved Amount", className="card-title"),
                            dcc.Slider(id="reserved_amount_slider", min=1, max=8, step=1, value=1),
                            html.Br(),
                            html.H5("Leave End", className="card-title"),
                            html.P(id='leave_end'),
                            html.Br(),
                            dcc.ConfirmDialogProvider(
                                children=html.Button('Click to take a leave',),
                                id='leave_button',
                                message='Ready to submit your day-off request. Pls double make sure it.'
                            ),
                        ]
                    ),
                    ]
    )
    leave_cards = dbc.Row(
        [
            dbc.Col(html.Div(), width='auto'),
            dbc.Col(leave_card, width=10),
            dbc.Col(html.Div(), width='auto'),
        ],
        justify="center"
    )
    total_leave_datatable_cards = dbc.Row(
        [
            dbc.Col(html.Div(), width='auto'),
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("Yearly Leave Form"),
                    dbc.CardBody([
                        html.P(id='leave_msg'),
                        html.Div(id='total_leave_datatable_div', style=table_style)
                    ])
                    ]), 
                    width=10),
            dbc.Col(html.Div(), width='auto'),
        ],
        justify="center"
    )

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

    leave_form = [html.Div([
        check_h1,
        leave_cards,
        html.Br(),
        total_leave_datatable_cards,
    ])]

    check_layout = [html.Div([
        check_h1,
        check_datepicker,
        check_datatable_div,
        sum_string,
        change_string,
        check_button,
        html.Br(),
        leave_datatable_div,
        html.Br(),
        check_link,
        html.Br(),
        home_link,
        personal_data_store,
        previous_check_store,
        agg_check_store,
        check_changes_store,
    ])]

    my_check_layout= [html.Div([
        check_h1,
        html.Div([year_dropdown, month_dropdown], style={"width": "25%"}),
        mycheck_datatable_div,
    ])]

    season_check_layout= [html.Div([
        check_h1,
        html.Div([year_dropdown, season_dropdown], style={"width": "25%"}),
        season_check_datatable_div,
    ])]


    # year and quarter picker for check_table
    @callback(
        [
            Output('season_check_datatable_div', 'children'),
            ],
        [
            Input('year_dropdown', 'value'),
            Input('season_dropdown', 'value'),
            ],
        [
            State('url', 'search'),
            State('url', 'pathname'),
            ]
        )
    def season_picker_check_table(year, season, search, pathname):
        staff = dict(parse_qsl(unquote(search))).get('?staff')
        print(staff)
        print(pathname)
        #print(int(datetime.strptime(month, "%b").month))
        #print(db.all_table_generator(year= int(year), month=int(datetime.strptime(month, "%b").month)).check_dataframe())
        check_df = db.season_table_generator(staff_name=staff, year=int(year), season=season).check_dataframe()
        print(check_df)

        return [
            check_table(check_df), 
        ]

    # month and year picker for check_table
    @callback(
        [
            Output('mycheck_datatable_div', 'children'),
            ],
        [
            Input('year_dropdown', 'value'),
            Input('month_dropdown', 'value'),
            ],
        [
            State('url', 'search'),
            State('url', 'pathname'),
            ]
        )
    def mypicker_check_table(year, month, search, pathname):
        staff = dict(parse_qsl(unquote(search))).get('?staff')
        #print(int(datetime.strptime(month, "%b").month))

        if 'date_check_all' in pathname:
        #print(db.all_table_generator(year= int(year), month=int(datetime.strptime(month, "%b").month)).check_dataframe())
            check_df = db.all_table_generator(year= int(year), month=int(datetime.strptime(month, "%b").month)).check_dataframe()
        else:
            pass

        return [
            check_table(check_df), 
        ]


    @callback(
    [   
        Output('leave_unit', 'children'),
        Output('reserved_amount_slider', 'max'),
        Output('leave_end', 'children'),
    ],
    [
        Input('leave_start_datetime_picker', 'value'),
        Input('reserved_amount_slider', 'value'),        
        Input('leave_type_radio', 'value'),
    ],
    )
    def update_on_leave_start_amount(leave_start, reserved_amount, leave_type) :
        _lst = [leave_start, reserved_amount, leave_type]
        if any(_arg == None for _arg in _lst):
            raise PreventUpdate
        else:
            #print(leave_start)
            leave_start = datetime.strptime(leave_start.split('.')[0], '%Y-%m-%dT%H:%M:%S')
            for k,v in db.leaves_type.items():
                if leave_type == v['type']:
                    _unit = v['unit']
                    _type = k
                    break
            leave_unit_children = f'Minimum {_unit}hr per {_type}'
            if _unit < 8:
                max = 8/_unit
                if reserved_amount > max:
                    reserved_amount = max
                #print(timedelta(hours=_unit*reserved_amount))
                leave_end = (leave_start + timedelta(hours=_unit*reserved_amount)).strftime("%Y-%m-%d %H:%M:%S")
                #print(leave_end)
            else:
                max = 5
                if reserved_amount > max:
                    reserved_amount = max
                leave_end = (leave_start + timedelta(days=_unit/8*reserved_amount)).strftime("%Y-%m-%d %H:%M:%S")
            return leave_unit_children, max, [leave_end]


    @callback(
        [
            Output('leave_msg', 'children'),
            Output('total_leave_datatable_div', 'children'),
        ],
        [
            Input('leave_button', 'submit_n_clicks'),
        ],
        [
            State('url', 'search'),
            State('url', 'pathname'),
            State('leave_type_radio', 'value'),
            State('leave_start_datetime_picker', 'value'),
            State('leave_end', 'children'),
            State('reserved_amount_slider', 'value'),
        ]
    )
    def take_a_leave_to_db(submit_n_clicks, search, pathname, leave_type, leave_start, leave_end, leave_reserved):
        staff_name = dict(parse_qsl(unquote(search))).get('?staff')
        staff=db.db_session.query(db.Staffs).filter(db.Staffs.staff_name==staff_name).scalar()
        start = datetime.strptime(leave_start.split('.')[0], '%Y-%m-%dT%H:%M:%S')
        leave_table_generator = db.table_generator(date(start.year, 1, 1), date(start.year, 12, 31), staff_name)

        leave_msg = 'Ready to take a leave. Pls Fill in all of leave_type, leave_start, leave_end, leave_reserved.'
        if submit_n_clicks:
            _lst = [leave_type, leave_start, leave_end, leave_reserved]
            if not any(_arg == None for _arg in _lst):
                # compare with record_range
                _start = datetime.strptime(leave_start, '%Y-%m-%dT%H:%M:%S')
                _end = datetime.strptime(leave_end[0],'%Y-%m-%d %H:%M:%S')
                _timerange_start = _start.strftime("%Y-%m-%d %H:%M:%S")
                _timerange_end = _end.strftime("%Y-%m-%d %H:%M:%S")
                _leave_timerange = DateTimeRange(_timerange_start, _timerange_end)
                _leave_daterange = pd.date_range(_start.date(), _end.date())
                bdays_hdays_df = leave_table_generator.calendar.bdays_hdays()
                _successful_record = True
                for i in staff.Leaves_time:
                    _record_start = i.start.strftime("%Y-%m-%d %H:%M:%S")
                    _record_end = i.end.strftime("%Y-%m-%d %H:%M:%S")
                    _record_range = DateTimeRange(_record_start, _record_end)
                    if (_leave_timerange in _record_range) or (_record_range in _leave_timerange) or (_timerange_start in _record_range) or (_timerange_end in _record_range):
                        _successful_record = False
                        leave_msg = f'Failed leave_record. Overlapping {_leave_timerange} to {_record_range}.'
                        break
                for i in _leave_daterange:
                    #print(bdays_hdays_df.loc[f'{i.date()}'])
                    if not bdays_hdays_df.loc[f'{i.date()}', 'Working Day']:
                        _successful_record = False
                        leave_msg = f'Failed leave_record. Overlapping {i} to {bdays_hdays_df.loc[f"{i.date()}", "weekday"]}.'
                        break

                if _successful_record:
                    end = datetime.strptime(leave_end[0], '%Y-%m-%d %H:%M:%S')
                    db.db_session.add(db.Leaves(
                        staff_name=staff_name, 
                        type=leave_type, 
                        start=start,
                        end=end,  
                        reserved=leave_reserved
                        ))
                    db.db_session.commit()    
                    leave_msg = 'Successful leave_record'
                    
        leave_df = leave_table_generator.leave_dataframe()
        if not leave_df.empty:
            leave_table = dash_table.DataTable(
                leave_df.to_dict('records'), 
                [{"name": i, "id": i} for i in leave_df.columns], 
                row_deletable=True,
                style_table={'overflowX': 'auto','minWidth': '100%',},
                style_cell={ 
                            'textAlign': 'center',               # ensure adequate header width when text is shorter than cell's text
                            'minWidth': '180px', 'maxWidth': '180px', 'width': '180px',
                            'whiteSpace': 'normal',
                            'height': '35px',
                            },
                style_header={
                            'backgroundColor': '#0074D9',
                            'color': 'white'
                            },
                )
        else:
            leave_msg = 'Empty leave_record'
            leave_table = None
        return [leave_msg], [leave_table]


    # datepicker for check_table
    @callback(
        [
            Output('check_datatable_div', 'children'),
            Output('previous_check_store', 'data'),
            Output('agg_check_store', 'data'),
            Output('sum_string', 'children'),
            Output('leave_datatable_div', 'children'),
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
        check_df, required_hours = db.table_generator(start_date, end_date, staff).check_dataframe()
        agg_check = check_df['aggregation[hr]'].iloc[0]

        # leave
        #leave_df = db.table_generator(start_date, end_date, staff).leave_dataframe()

        return [
            check_table(check_df), 
            check_df.to_json(orient='split', date_format='iso'),
            agg_check,
            [html.Div(f"This month till now, u've worked for {agg_check} [hr]."), 
            html.Div(f"Required hours: {required_hours} [hr]."), 
            html.Div(f"Working Hour Difference: {agg_check - required_hours} [hr]"),],
            None
            #check_table(leave_df)
        ]


    # only the last 30 row could be editable
    # match certin string format
    r = re.compile('\d{2}:\d{2}:\d{2}')
    @callback(
        Output('check_datatable', 'data'),
        Input('check_datatable', 'data_timestamp'),
        [State('check_datatable', 'data'),
        State('previous_check_store', 'data'),]
        )
    def update_lastcells(timestamp, data, data_previous):
        print(data)
        data_previous = pd.read_json(data_previous, orient='split').to_dict(orient='records')
        if (data != None) and (data_previous) != None:
            for i in range(len(data)):
                for col in ['checkin', 'checkout']:
                    if data[i][col] is not None:
                        if (r.match(data[i][col]) is None):
                            data[i][col] = 'HH:MM:SS'
                    if i >= 30:
                        #print(i, data[i][col], data_previous[i][col])
                        data[i][col] = data_previous[i][col]
                    else:
                        pass
            return data


    # only the last three row could be editable
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
    

    # route to check_layout / index_page / leave_form
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
        
        # datetime init
        check_datepicker.initial_visible_month = datetime.now().date()
        check_datepicker.start_date = (datetime.now().date()  - pd.offsets.MonthBegin(1)).date()
        check_datepicker.end_date = datetime.now().date()

        leave_start_datetime_picker.value = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        config.logging.debug([pathname, search])
        check_type = pathname.split(f'{url_prefix}')[-1]
        staff = dict(parse_qsl(unquote(search))).get('?staff')
        personal_data_store.data = {'staff':staff}
        config.logging.debug([check_type, staff])

        if 'date_check' in check_type:
            other_type = '/season_check'
            check_link.children = staff + other_type
            check_link.href = url_prefix + other_type + search
        elif '/season_check' in check_type:
            other_type = '/date_check'
            check_link.children = staff + other_type
            check_link.href = url_prefix + other_type + search
        elif 'leave_form' in check_type:
            pass
        
        check_h1.children = staff + check_type
        home_link.children = staff + '/Sweet Home'
        home_link.href = url_prefix + search

        if check_type == '/date_check':
            return check_layout
        elif check_type == '/season_check':
            return season_check_layout
        elif check_type == '/date_check_all':
            return my_check_layout
        elif check_type == '/season_check_all':
            return season_check_layout
        elif check_type == '/leave_form':
            return leave_form
        else:
            return index_page
        # You could also return a 404 "URL not found" page here