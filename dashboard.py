# library
from distutils.log import debug
from dash import Dash, dcc, html, callback, Input, Output, dash_table, State
from dash.dash_table import DataTable
from dash.exceptions import PreventUpdate
from urllib.parse import urlparse, unquote, parse_qsl
import dash_bootstrap_components as dbc
from datetime import datetime, date, timedelta
from datetime import time as datetime_time 
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
                                'minWidth': '140px', 'maxWidth': '220px', 'width': '200px',
                                'fontSize':26, 'font-family':'sans-serif'
                                },
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
                                        'filter_query': '{weekday} != Mon && {weekday} != Tue && {weekday} != Wed && {weekday} != Thu && {weekday} != Fri',
                                        'column_id': ['date', 'weekday']
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
                                    column: {'value': f'Edit with following format: "HH:MM"', 'type': 'markdown'}
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
                            dbc.CardGroup(
                                [
                                    dbc.Card(
                                        dbc.CardBody(
                                            [
                                                html.H5("Leave Type", className="card-title"),
                                                html.P(id='leave_unit'),
                                                dcc.RadioItems(
                                                    id="leave_type_radio",
                                                    options={v['type']:k for (k,v) in db.leaves_type.items()},
                                                    style={'width':'70%', 'font-size': 26}
                                                ),
                                            ]
                                        ),
                                        className="mb-3",
                                    ),
                                    dbc.Card(
                                        dbc.CardBody(
                                            [
                                                html.Div(id='leave_quota_datatable_div', style=table_style)
                                            ]
                                        ),
                                        className="mb-3",
                                    ),
                                ],
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
            dbc.Col(leave_card, width=11),
            dbc.Col(html.Div(), width='auto'),
        ],
        justify="center"
    )
    total_leave_datatable_cards = dbc.Row(
        [
            dbc.Col(html.Div(), width='auto'),
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("Yearly Leave Table"),
                    dbc.CardBody([
                        html.P(id='leave_msg'),
                        html.Div(id='total_leave_datatable_div', style=table_style)
                    ])
                    ]), 
                    width=11),
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
        dbc.Row(
            [
                dbc.Col(html.Div(), width='auto'),
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader("Datepicker Check Table"),
                        dbc.CardBody([
                            check_datepicker,
                            check_datatable_div,
                            change_string,
                            check_button,
                        ])
                        ]), 
                        width=11),
                dbc.Col(html.Div(), width='auto'),
            ],
            justify="center"
        ),
        dbc.Row(
            [
                dbc.Col(html.Div(), width='auto'),
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody([
                            html.Div(id='sum_string'),
                        ])
                        ]), 
                        width=10),
                dbc.Col(html.Div(), width='auto'),
            ],
            justify="center"
        ),
        personal_data_store,
        previous_check_store,
        agg_check_store,
        check_changes_store,
    ])]

    my_check_layout= [html.Div([
        check_h1,
        dbc.Row(
            [
                dbc.Col(html.Div(), width='auto'),
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader("Monthly All Check Table"),
                        dbc.CardBody([
                            html.Div([year_dropdown, month_dropdown], style={"width": "25%"}),
                            html.Br(),
                            html.Div(id='mycheck_datatable_div', style=table_style)
                        ])
                        ]), 
                        width=11),
                dbc.Col(html.Div(), width='auto'),
            ],
            justify="center"
        ),
    ])]

    season_check_layout= [html.Div([
        check_h1,
        dbc.Row(
            [
                dbc.Col(html.Div(), width='auto'),
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader("Seasonal Check Table"),
                        dbc.CardBody([
                            html.Div([year_dropdown, season_dropdown], style={"width": "25%"}),
                            html.Br(),
                            html.Div(id='season_1st_datatable_div', style=table_style),
                            html.Br(),
                            html.Div(id='season_2nd_datatable_div', style=table_style),
                            html.Br(),
                            html.Div(id='season_3rd_datatable_div', style=table_style),
                            html.Br(),
                            html.Div(id='season_total_datatable_div', style=table_style),
                        ])
                        ]), 
                        width=11),
                dbc.Col(html.Div(), width='auto'),
            ],
            justify="center"
        ),
    ])]


    # year and quarter picker for check_table
    @callback(
        [
            Output('season_1st_datatable_div', 'children'),
            Output('season_2nd_datatable_div', 'children'),
            Output('season_3rd_datatable_div', 'children'),
            Output('season_total_datatable_div', 'children'),
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
        #print(staff)
        #print(pathname)
        if season == None:
            raise PreventUpdate
        else:
            df_lst = db.season_table_generator(staff_name=staff, year=int(year), season=season).check_dataframe()
            table_lst = []
            for df in df_lst:
                table = dash_table.DataTable(
                    df.to_dict('records'), 
                    [{"name": i, "id": i} for i in df.columns], 
                    id='season_table',
                    style_table={'overflowX': 'auto','minWidth': '100%',},
                    style_cell={ 
                                'textAlign': 'center',               # ensure adequate header width when text is shorter than cell's text
                                'minWidth': '180px', 'maxWidth': '180px', 'width': '180px',
                                'whiteSpace': 'normal',
                                'height': '35px',
                                'fontSize':26, 'font-family':'sans-serif'
                                },
                    style_header={
                                'backgroundColor': '#0074D9',
                                'color': 'white'
                                },
                    )
                table_lst.append(table)
            return table_lst

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
            all_check_df = db.all_table_generator(year= int(year), month=int(datetime.strptime(month, "%b").month)).check_dataframe()
            all_table = dash_table.DataTable(
                all_check_df.to_dict('records'), 
                [{"name": i, "id": i} for i in all_check_df.columns], 
                id='all_table',
                filter_action="native",
                page_action="native",
                page_current= 0,
                page_size= 10,
                style_table={'overflowX': 'auto','minWidth': '100%',},
                style_cell={ 
                            'textAlign': 'center',               # ensure adequate header width when text is shorter than cell's text
                            'minWidth': '180px', 'maxWidth': '180px', 'width': '180px',
                            'whiteSpace': 'normal',
                            'height': '35px',
                            'fontSize':26, 'font-family':'sans-serif'
                            },
                style_header={
                            'backgroundColor': '#0074D9',
                            'color': 'white'
                            },
                )

        return [all_table]


    # leave_quota init
    @callback(
        Output('leave_quota_datatable_div', 'children'),
        [
            Input('leave_type_radio', 'value'),
            Input('leave_table', 'data'),
            ],
        [
            State('url', 'search'),
            State('url', 'pathname'),
            ]
        )
    def leave_quota_table(leave_type, leave_table, search, pathname):
        staff = dict(parse_qsl(unquote(search))).get('?staff')
        df_leave_quota = db.staffs_datatable_generator(staff).staffs_datatable()
        leave_quota_table = dash_table.DataTable(
            df_leave_quota.to_dict('records'), 
            [{"name": i, "id": i} for i in df_leave_quota.columns], 
            id='leave_quota_table',
            style_table={'overflowX': 'auto','minWidth': '100%',},
            style_cell={ 
                        'textAlign': 'center',               # ensure adequate header width when text is shorter than cell's text
                        'minWidth': '80px', 'maxWidth': '180px', 'width': '120px',
                        'whiteSpace': 'normal',
                        'height': '35px',
                        'fontSize':22, 'font-family':'sans-serif'
                        },
            style_header={
                        'backgroundColor': '#0074D9',
                        'color': 'white'
                        },
            )
        return leave_quota_table


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
                leave_end = (leave_start.replace(day=leave_start.day+reserved_amount-1, hour=17, minute=30, second=0)).strftime("%Y-%m-%d %H:%M:%S")
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
        # Yearly leave 
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
                    # add to leaves table
                    db.db_session.add(db.Leaves(
                        staff_name=staff_name, 
                        type=leave_type, 
                        start=start,
                        end=end,  
                        reserved=leave_reserved
                        ))
                    
                    # update staff quota
                    for k,v in db.leaves_type.items():
                        if leave_type == v['type']:
                            _unit = v['unit']/8
                            _type = k
                            break
                    cur_quota = db.db_session.query(db.Staffs).filter(db.Staffs.staff_name == staff_name).scalar().__dict__.get(_type)
                    print(cur_quota)
                    updated_quota = cur_quota - leave_reserved*_unit
                    print(updated_quota)
                    db.db_session.query(db.Staffs).\
                    filter(db.Staffs.staff_name == staff_name).\
                    update({f"{_type}": updated_quota})

                    leave_msg = 'Successful leave_record'
                    db.db_session.commit()
                    
        leave_df = leave_table_generator.leave_dataframe()
        if not leave_df.empty:
            leave_table = dash_table.DataTable(
                leave_df.to_dict('records'), 
                [{"name": i, "id": i} for i in leave_df.columns], 
                id='leave_table',
                filter_action="native",
                row_deletable=True,
                page_action="native",
                page_current= 0,
                page_size= 10,
                export_format='xlsx',
                export_headers='display',
                style_table={'overflowX': 'auto','minWidth': '100%',},
                style_cell={ 
                            'textAlign': 'center',               # ensure adequate header width when text is shorter than cell's text
                            'minWidth': '130px', 'maxWidth': '200px', 'width': '180px',
                            'whiteSpace': 'normal',
                            'height': '35px',
                            'fontSize':26, 'font-family':'sans-serif'
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


    # update the leave table         
    @callback(
    [
        Output('leave_table', 'data'), 
        ],
    [
        Input('leave_table', 'data'),
        ],
    [
        State('url', 'search'),
        State('leave_table', 'data_previous'),
        ],
    prevent_initial_call=True,
    )
    def update_leave_data(data, search, data_previous):
        print(data)
        print(data_previous)
        staff_name = dict(parse_qsl(unquote(search))).get('?staff')
        if data == data_previous:
            raise PreventUpdate
        else:
            if (data != None) and (data_previous != None):
                _del_index = data_previous[-1]['index']
                for i in range(len(data)):
                    if data[i]['index'] != data_previous[i]['index']:
                        _del_index = int(data_previous[i]['index'])
                db.db_session.query(db.Leaves).\
                filter(db.Leaves.id == _del_index, db.Leaves.staff_name == staff_name).\
                delete()
                db.db_session.commit()
            #refresh the page
            return [data]


    # datepicker for check_table
    @callback(
        [
            Output('check_datatable_div', 'children'),
            Output('previous_check_store', 'data'),
            #Output('agg_check_store', 'data'),
            Output('sum_string', 'children'),
            ],
        [
            Input('check_datepicker', 'start_date'),
            Input('check_datepicker', 'end_date'),
            Input('url', 'search'),
            ],
        )
    def datepicker_check_table(start_date, end_date, search):
        #print(f'{search} from datepicker_check_table')
        staff = dict(parse_qsl(unquote(search))).get('?staff')
        #print(start_date)
        #print(end_date)
        check_df, required_hours = db.table_generator(start_date, end_date, staff).check_dataframe()
        workhour = sum(check_df['worktime[hr]'].iloc[:])
        leavehour = sum(check_df['leave_amount[hr]'].iloc[:])

        # leave
        #leave_df = db.table_generator(start_date, end_date, staff).leave_dataframe()

        return [
            check_table(check_df), 
            check_df.to_json(orient='split', date_format='iso'),
            [html.Div(f"Working hours: {workhour} [hr]"),
            html.Div(f"Leaving hours {leavehour} [hr]"), 
            html.Div(f"Required hours: {required_hours} [hr]"), 
            html.Div(f"Difference: {round(leavehour + workhour - required_hours,2)} [hr]"),],
        ]


    # only the last 30 row could be editable
    # match certin string format
    r = re.compile('\d{2}:\d{2}')
    @callback(
        Output('check_datatable', 'data'),
        [Input('check_datatable', 'data'),],
        [State('check_datatable', 'data_previous'),]
        )
    def update_lastcells(data, data_previous):
        #print(data)
        #print(data_previous)
        if data_previous is None:
            return data
        else:
            for i in range(len(data)):
                for col in ['checkin', 'checkout']:
                    # input format regular expression
                    if data[i][col] is not None:
                        if (r.match(data[i][col]) is None):
                            data[i][col] = None
                        else:
                            _hour = data[i][col][0:2]
                            _minute = data[i][col][3:]
                            #print(_hour, _minute)
                            if int(_hour) <= 0 or int(_hour) >= 23 or int(_minute) <= 0 or int(_minute) >= 59:
                                data[i][col] = None
                    # Restrict Editable time to 31 days
                    if i >= 31:
                        #print(i, data[i][col], data_previous[i][col])
                        data[i][col] = data_previous[i][col]
                # check in <= checkout
                if data[i]['checkin'] != None and data[i]['checkout'] != None:
                    #print(data[i]['checkin'])
                    #print(data[i]['checkout'])
                    if datetime_time(int(data[i]['checkin'][0:2]), int(data[i]['checkin'][3:])) >= datetime_time(int(data[i]['checkout'][0:2]), int(data[i]['checkout'][3:])):
                        data[i]['checkin'] = data_previous[i]['checkin']
                        data[i]['checkout'] = data_previous[i]['checkout']
            return data

    # update the check table         
    @callback(
    [
        Output('url', 'refresh'),
        Output('url', 'href'),
        Output('change_string', 'children'), 
        ],
    [
        Input('check_button', 'submit_n_clicks'),
        ],
    [
        State('url', 'search'),
        State('url', 'pathname'),
        State('check_datatable', 'data'),
        State('check_datatable', 'data_previous'),
        ],
    prevent_initial_call=False,
    )
    def update_check_data(submit_n_clicks, search, pathname, data, data_previous):
        #print(data) # list of dictionaries of str or None
        #print(data_previous)
        staff_name = dict(parse_qsl(unquote(search))).get('?staff')
        if not submit_n_clicks:
            raise PreventUpdate
        else:
            if (data != None) and (data_previous) != None:
                changes = {}
                for i in range(len(data)):
                    if data[i] != data_previous[i]:
                        for col in ('checkin', 'checkout'):
                            if data[i][col] != data_previous[i][col]:
                                current_datetime = data[i]['date'] + ' ' + data[i][col] if data[i][col] != None else None
                                pre_datetime = data_previous[i]['date'] + ' ' + data_previous[i][col] if data_previous[i][col] != None else None
                                changes[i] = {'col':col, 'previous': pre_datetime, 'current': current_datetime}
                print(changes)

                for key, value in changes.items():
                    #print(key, value)
                    col = value['col']
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
                            pre = datetime.strptime(pre, '%m/%d/%Y %H:%M')
                        except Exception as e:
                            return [False, f"{pathname}{search}", str(e),]
                        #delete the row
                        db.db_session.query(table).\
                        filter(table.staff_name == staff_name, table.created_time == pre).\
                        delete()
                    elif pre == None:
                        try:
                            cur = datetime.strptime(cur, '%m/%d/%Y %H:%M')
                        except Exception as e:
                            return [False, f"{pathname}{search}", str(e),]
                        # insert a row
                        db.db_session.add(table(staff_name=staff_name, created_time=cur))
                    else:
                        try:
                            pre = datetime.strptime(pre, '%m/%d/%Y %H:%M')
                            cur = datetime.strptime(cur, '%m/%d/%Y %H:%M')
                            #print(pre, cur)
                        except Exception as e:
                            return [False, f"{pathname}{search}", str(e),]
                        # update the row
                        db.db_session.query(table).\
                        filter(table.staff_name == staff_name, table.created_time == pre).\
                        update({"created_time": cur})
            db.db_session.commit()
            #refresh the page
            return [True, f"{pathname}{search}", 'Succeed',]


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

        if 'date_check?' in check_type:
            other_type = '/season_check'
            #check_link.children = staff + other_type
            #check_link.href = url_prefix + other_type + search
        elif '/season_check' in check_type:
            other_type = '/date_check'
            #check_link.children = staff + other_type
            #check_link.href = url_prefix + other_type + search
        elif 'leave_form' in check_type:
            pass
        
        check_h1.children = str(staff) + check_type
        #home_link.children = staff + '/Sweet Home'
        #home_link.href = url_prefix + search

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