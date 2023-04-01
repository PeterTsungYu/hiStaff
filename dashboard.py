# library
from distutils.log import debug
from dash import Dash, dcc, html, callback, Input, Output, dash_table, State, ctx
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
    check_h2 = html.H2(id='check_h2')
    check_datepicker = dcc.DatePickerRange(
                        id='check_datepicker',
                        min_date_allowed=date(1992, 1, 25),
                        max_date_allowed=date(2100, 1, 25),
                        initial_visible_month=datetime.now().date(),
                        start_date=(datetime.now().date()  - pd.offsets.MonthBegin(1)).date(),
                        end_date=datetime.now().date(),
    )
    check_link = dcc.Link(id='check_link', href=f'{url_prefix}/')
    home_link = dcc.Link(id='home_link', href=f'{url_prefix}/')
    index_dropdown = dcc.Dropdown(['check', 'Season'], 'check', id='index_dropdown')
    month_dropdown = dcc.Dropdown(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], datetime.now().strftime("%b"), id='month_dropdown', placeholder="Select A Month",)
    year_dropdown = dcc.Dropdown(['2022', '2023', '2024', '2025', '2026'], datetime.now().strftime("%Y"), id='year_dropdown', placeholder="Select A Year",)
    #season_dropdown = dcc.Dropdown(['Q1', 'Q2', 'Q3', 'Q4'], 'Q1', id='season_dropdown', placeholder="Select A Quarter",)
    season_dropdown = dcc.RadioItems(
        id="season_dropdown",
        options=['Q1', 'Q2', 'Q3', 'Q4'],
        style={'width':'80%', 'font-size': 18}
    )
    check_dropdown = dcc.Dropdown(['Monthly Report', 'CheckIn Report', 'CheckOut Report', 'Leave Report'], 'Monthly Report', id='check_dropdown', placeholder="Report",)

    def check_table(check_df):
        #print(check_df.columns)
        datatable = DataTable(
                            id='check_datatable',
                            # columns=[{"name": i, "id": i, "deletable": False, "selectable": False, "editable":True} if i in ['checkin', 'checkout'] else {"name": i, "id": i, "deletable": False, "selectable": False, "editable":False} for i in check_df.columns],
                            columns=[
                                {"name": '日期', "id": 'date' , "deletable": False, "selectable": False, "editable": False},
                                {"name": '星期', "id": 'weekday' , "deletable": False, "selectable": False, "editable": False},
                                {"name": '上班打卡', "id": 'checkin' , "deletable": False, "selectable": False, "editable": True},
                                {"name": '上班地點', "id": 'location_in' , "deletable": False, "selectable": False, "editable": False},
                                {"name": '下班打卡', "id": 'checkout' , "deletable": False, "selectable": False, "editable": True},
                                {"name": '下班地點', "id": 'location_out' , "deletable": False, "selectable": False, "editable": False},
                                {"name": '當日工作時數', "id": 'worktime[hr]' , "deletable": False, "selectable": False, "editable": False},
                                {"name": '請假開始時間', "id": 'leave_start' , "deletable": False, "selectable": False, "editable": False},
                                {"name": '請假時數', "id": 'leave_amount[hr]' , "deletable": False, "selectable": False, "editable": False},
                                {"name": '累計時數', "id": 'aggregation[hr]' , "deletable": False, "selectable": False, "editable": False},
                                ],
                            data=check_df.to_dict('records'),
                            editable=True,
                            #filter_action="native",
                            #sort_action="native",
                            #sort_mode="multi",
                            page_action="native",
                            page_current= 0,
                            page_size= 15,
                            style_table={'overflowX': 'auto','minWidth': '50%',},
                            style_cell={ 
                                'textAlign': 'center',               # ensure adequate header width when text is shorter than cell's text
                                'minWidth': '120px', 'maxWidth': '300px', 'width': '120px',
                                'fontSize':18, 'font-family':'sans-serif'
                                },
                            style_data={                # overflow cells' content into multiple lines
                                #'whiteSpace': 'normal',
                                'height': 'auto'
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
                                    column: {'value': f'以此時間格式進行修改: "HH:MM"', 'type': 'markdown'}
                                    if column in ['checkin', 'checkout']
                                    else f"{value}"
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
    leave_start_datetime_picker = dcc.Input(id='leave_start_datetime_picker', type="datetime-local", step="1", style={'height': '40px', 'font-size': "20px",},)
    leave_card = dbc.Card([
                    dbc.CardHeader("Leave Form"),
                    dbc.CardBody(
                        [
                            check_h2,
                            dbc.CardGroup(
                                [
                                    dbc.Card(
                                        dbc.CardBody(
                                            [
                                                html.H3("Leave Type", className="card-title"),
                                                html.P(id='leave_unit'),
                                                dcc.RadioItems(
                                                    id="leave_type_radio",
                                                    options={v['type']:k for (k,v) in db.leaves_type.items()},
                                                    style={'width':'80%', 'font-size': 18}
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
                            html.H2("Leave Start", className="card-title"),
                            leave_start_datetime_picker,
                            html.Br(),
                            html.Br(),
                            html.H2("Reserved Amount", className="card-title"),
                            dcc.Slider(id="reserved_amount_slider", min=1, max=8, step=1, value=1),
                            html.Br(),
                            html.H2("Leave End", className="card-title"),
                            html.H4(id='leave_end'),
                            html.Br(),
                            html.Div(id='leave_entry'),
                            html.P(id='leave_msg'),
                            dcc.ConfirmDialogProvider(
                                children=html.Button('Click to take a leave', style={'height': '60px', 'font-size': "20px",}),
                                id='leave_button',
                                message='Ready to submit your day-off request. Pls double make sure it.',
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
                        html.H4("Leave Datatable: Future", className="card-title"),
                        html.Div(id='total_leave_datatable_future_div', style=table_style),
                        html.Br(),
                        html.H4("Leave Datatable: Past", className="card-title"),
                        html.Div(id='total_leave_datatable_past_div', style=table_style),
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
    leave_form = [html.Div([
        leave_cards,
        html.Br(),
        total_leave_datatable_cards,
    ])]

    check_layout = [html.Div([
        dbc.Row(
            [
                dbc.Col(html.Div(), width='auto'),
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader("專屬的個人打卡紀錄表"),
                        dbc.CardBody([
                            check_h2,
                            check_datepicker,
                            html.Div(id='check_datatable_div', style=table_style),
                            html.Br(),
                            html.Br(),
                            html.H5(id='change_string'),
                            dcc.Input(
                                id='check_revision_reason', 
                                type='text',
                                required=True,
                                placeholder="在此輸入你的修改理由...",
                                style={'height': '60px', 'font-size': "22px",},
                                ),
                            html.Br(),
                            html.Br(),
                            dcc.ConfirmDialogProvider(
                                children=html.Button('送出修改的打卡紀錄', style={'height': '60px', 'font-size': "18px",}),
                                id='check_button',
                                message='即將送出修改，請再次確認修改的時間格'
                                ),
                        ])
                        ]), 
                        width=11),
                dbc.Col(html.Div(), width='auto'),
            ],
            justify="center"
        ),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(html.Div(), width='auto'),
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader("時數摘要"),
                        dbc.CardBody([
                            html.Div(id='sum_string'),
                        ])
                        ]), 
                        width=11),
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
        dbc.Row(
            [   
                dbc.Col(html.Div(), width='auto'),
                dbc.Col(
                    dbc.Card([
                        #dbc.CardHeader("Index"),
                        dbc.CardBody([
                            dcc.Link('Go to Seasonal Report', id='link_season_check_all', href='/hiStaff_dashapp/season_check_all'),
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
                        dbc.CardHeader("Monthly All Check Table"),
                        dbc.CardBody([
                            check_h2,
                            html.Div([year_dropdown, month_dropdown, check_dropdown], style={"width": "25%"}),
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
        dbc.Row(
            [   
                dbc.Col(html.Div(), width='auto'),
                dbc.Col(
                    dbc.Card([
                        #dbc.CardHeader("Index"),
                        dbc.CardBody([
                            dcc.Link('Go to Check Report', id='link_date_check_all', href='/hiStaff_dashapp/date_check_all'),
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
                        dbc.CardHeader("Seasonal Check Table"),
                        dbc.CardBody([
                            check_h2,
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
        _uuid = dict(parse_qsl(unquote(search))).get('?staff')
        staff = db.db_session.query(db.Staffs).filter(db.Staffs.uuid==_uuid).scalar()
        #print(staff)
        #print(pathname)
        if season == None:
            raise PreventUpdate
        else:
            df_lst = db.season_table_generator(staff=staff if staff else 'All', year=int(year), season=season).check_dataframe()
            table_lst = []
            for df in df_lst:
                table = dash_table.DataTable(
                    df.to_dict('records'), 
                    [{"name": i, "id": i} for i in df.columns], 
                    id='season_table',
                    style_table={'overflowX': 'auto','minWidth': '100%',},
                    style_cell={ 
                                'textAlign': 'center',               # ensure adequate header width when text is shorter than cell's text
                                'minWidth': '100px', 'maxWidth': '100px', 'width': '100px',
                                'fontSize':16, 'font-family':'sans-serif'
                                },
                    style_data={                # overflow cells' content into multiple lines
                            'whiteSpace': 'normal',
                            'height': 'auto'
                        },
                    style_header={
                                'backgroundColor': '#0074D9',
                                'color': 'white'
                                },
                    export_format='xlsx',
                    export_headers='display',
                    )
                table_lst.append(table)
            return table_lst

    # /date_check_all
    @callback(
        Output('mycheck_datatable_div', 'children'),
        [
            Input('year_dropdown', 'value'),
            Input('month_dropdown', 'value'),
            Input('check_dropdown', 'value'),
            ],
        )
    def mypicker_check_table(year, month, check_dropdown):
        _lst = [year, month, check_dropdown]
        if any(_arg == None for _arg in _lst):
            raise PreventUpdate
        #print(int(datetime.strptime(month, "%b").month))
        #print(db.all_table_generator(year= int(year), month=int(datetime.strptime(month, "%b").month)).check_dataframe())
        if check_dropdown == 'Monthly Report':
            all_check_df = db.all_table_generator(year= int(year), month=int(datetime.strptime(month, "%b").month)).check_dataframe()
            id = 'monthly_all_check_dataframe'
            row_deletable = False
        elif check_dropdown == 'CheckIn Report':
            all_check_df = db.all_table_generator(year= int(year), month=int(datetime.strptime(month, "%b").month)).check_in_out_dataframe('CheckIn')
            id = 'monthly_all_checkin_dataframe'
            row_deletable = False
        elif check_dropdown == 'CheckOut Report':
            all_check_df = db.all_table_generator(year= int(year), month=int(datetime.strptime(month, "%b").month)).check_in_out_dataframe('CheckOut')
            id = 'monthly_all_checkout_dataframe'
            row_deletable = False
        elif check_dropdown == 'Leave Report':
            all_check_df = db.all_table_generator(year= int(year), month=int(datetime.strptime(month, "%b").month)).leave_dataframe()
            id = 'monthly_all_leave_dataframe'
            row_deletable = True
        else:
            all_check_df = pd.DataFrame()
            id = 'monthly_all_empty'
            row_deletable = False

        if not all_check_df.empty:
            all_table = dash_table.DataTable(
                all_check_df.to_dict('records'), 
                [{"name": i, "id": i} for i in all_check_df.columns], 
                id=id,
                filter_action="native",
                page_action="native",
                page_current= 0,
                page_size= 20,
                row_deletable=row_deletable,
                style_table={'overflowX': 'auto','minWidth': '100%',},
                style_cell={ 
                            'textAlign': 'center',               # ensure adequate header width when text is shorter than cell's text
                            'minWidth': '100px', 'maxWidth': '100px', 'width': '100px',
                            'fontSize':16, 'font-family':'sans-serif'
                            },
                style_data={                # overflow cells' content into multiple lines
                    'whiteSpace': 'normal',
                    'height': 'auto'
                    },
                style_header={
                            'backgroundColor': '#0074D9',
                            'color': 'white'
                            },
                export_format='xlsx',
                export_headers='display',
                )
        else:
            all_table = dash_table.DataTable(
                all_check_df.to_dict('records'), 
                id=id,
                row_deletable=row_deletable,
                )
        return all_table


    # leave_quota init
    @callback(
        Output('leave_quota_datatable_div', 'children'),
        [
            Input('check_h2', 'children'),
            Input('leave_table_future', 'data'),
            ],
        [
            State('url', 'search'),
            State('url', 'pathname'),
            ],
        #prevent_initial_call=False,
        )
    def leave_quota_table(check_h2, data, search, pathname):
        print('leave_quota_table')
        _uuid = dict(parse_qsl(unquote(search))).get('?staff')
        staff = db.db_session.query(db.Staffs).filter(db.Staffs.uuid==_uuid).scalar()
        df_leave_quota = db.staffs_datatable_generator(staff).staffs_datatable()
        leave_quota_table = dash_table.DataTable(
            df_leave_quota.to_dict('records'), 
            [{"name": i, "id": i} for i in df_leave_quota.columns], 
            id='leave_quota_table',
            style_table={'overflowX': 'auto','minWidth': '100%',},
            style_cell={ 
                        'textAlign': 'center',               # ensure adequate header width when text is shorter than cell's text
                        'minWidth': '80px', 'maxWidth': '120px', 'width': '800px',
                        'fontSize':14, 'font-family':'sans-serif'
                        },
            style_data={                # overflow cells' content into multiple lines
                'whiteSpace': 'normal',
                'height': 'auto'
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
        Output('leave_entry', 'children'),
    ],
    [
        Input('leave_start_datetime_picker', 'value'),
        Input('reserved_amount_slider', 'value'),        
        Input('leave_type_radio', 'value'),
    ],
    State('reserved_amount_slider', 'max'),
    )
    def update_on_leave_start_amount(leave_start, reserved_amount, leave_type, max) :
        _lst = [leave_start, reserved_amount, leave_type]
        if any(_arg == None for _arg in _lst):
            leave_unit_children = 'Pls select a type'
            leave_end = 'Pls select a type'
            leave_entry = dcc.Markdown(
                f'''
                    Ready to take a leave
                    Pls Fill in all of 
                    * leave_type
                    * leave_start
                    * leave_end
                    * leave_reserved
                ''')
            return leave_unit_children, max, leave_end, leave_entry
            
        else:
            #print(leave_start)
            try:
                leave_start = datetime.strptime(leave_start.split('.')[0], '%Y-%m-%dT%H:%M:%S')
            except:
                leave_start = datetime.strptime(leave_start.split('.')[0], '%Y-%m-%dT%H:%M')
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
                if reserved_amount > 1:
                    leave_end = ((leave_start + timedelta(days=reserved_amount-1)).replace(hour=17, minute=30, second=0)).strftime("%Y-%m-%d %H:%M:%S")
                else:
                    leave_end = (leave_start + timedelta(hours=_unit*reserved_amount)).strftime("%Y-%m-%d %H:%M:%S")
            leave_entry = dcc.Markdown(
                f'''
                    * From {leave_start}
                    * To {leave_end}
                    * {_type}: {_unit}*{reserved_amount} hr
                ''')
            return leave_unit_children, max, leave_end, leave_entry


    @callback(
        [
            Output('leave_msg', 'children'),
            Output('total_leave_datatable_past_div', 'children'),
            Output('total_leave_datatable_future_div', 'children'),
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
        ],
    )
    def take_a_leave_to_db(submit_n_clicks, search, pathname, leave_type, leave_start, leave_end, leave_reserved):
        print('take_a_leave_to_db')
        _uuid = dict(parse_qsl(unquote(search))).get('?staff')
        staff=db.db_session.query(db.Staffs).filter(db.Staffs.uuid==_uuid).scalar()
        try:
            start = datetime.strptime(leave_start.split('.')[0], '%Y-%m-%dT%H:%M:%S')
        except:
            start = datetime.strptime(leave_start.split('.')[0], '%Y-%m-%dT%H:%M')
        # Yearly leave 
        leave_table_generator = db.table_generator(date(start.year, 1, 1), date(start.year, 12, 31), staff)

        leave_msg = None
        if submit_n_clicks:
            _lst = [leave_type, leave_start, leave_end, leave_reserved]
            if not any(_arg == None for _arg in _lst):
                # compare with record_range
                try:
                    _start = datetime.strptime(leave_start, '%Y-%m-%dT%H:%M:%S')
                except:
                    _start = datetime.strptime(leave_start, '%Y-%m-%dT%H:%M')
                #print(leave_end)
                _end = datetime.strptime(leave_end,'%Y-%m-%d %H:%M:%S')
                try:
                    _timerange_start = _start.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    _timerange_start = _start.strftime("%Y-%m-%d %H:%M")
                _timerange_end = _end.strftime("%Y-%m-%d %H:%M:%S")
                _leave_timerange = DateTimeRange(_timerange_start, _timerange_end)
                _leave_daterange = pd.date_range(_start.date(), _end.date())
                bdays_hdays_df = leave_table_generator.calendar.bdays_hdays()
                _successful_record = True
                for i in staff.Leaves_time:
                    if _start > _end:
                        _successful_record = False
                        leave_msg = f'time inversion found: {_start} > {_end}'
                        break
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
                    end = datetime.strptime(leave_end, '%Y-%m-%d %H:%M:%S')
                    # add to leaves table
                    db.db_session.add(db.Leaves(
                        staff_name=staff.staff_name, 
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
                    cur_quota = db.db_session.query(db.Staffs).filter(db.Staffs.staff_name == staff.staff_name).scalar().__dict__.get(_type)
                    print(cur_quota)
                    updated_quota = cur_quota - leave_reserved*_unit
                    print(updated_quota)
                    db.db_session.query(db.Staffs).\
                    filter(db.Staffs.staff_name == staff.staff_name).\
                    update({f"{_type}": updated_quota})

                    leave_msg = 'Successful leave_record'
                    db.db_session.commit()
                    
        leave_df_past, leave_df_future = leave_table_generator.leave_dataframe()
        leave_datatable_lst = []
        for span in ['past', 'future']:
            if span == 'past':
                leave_df = leave_df_past
                id = 'leave_table_past'
                row_deletable = False
            elif span == 'future':
                leave_df = leave_df_future
                id = 'leave_table_future'
                row_deletable = True
            if not leave_df.empty:
                leave_table = dash_table.DataTable(
                    leave_df.to_dict('records'), 
                    [{"name": i, "id": i} for i in leave_df.columns], 
                    id=id,
                    filter_action="native",
                    row_deletable=row_deletable,
                    page_action="native",
                    page_current= 0,
                    page_size= 10,
                    export_format='xlsx',
                    export_headers='display',
                    style_table={'overflowX': 'auto','minWidth': '100%',},
                    style_cell={ 
                                'textAlign': 'center',               # ensure adequate header width when text is shorter than cell's text
                                'minWidth': '100px', 'maxWidth': '150px', 'width': '100px',
                                'fontSize':18, 'font-family':'sans-serif'
                                },
                    style_data={                # overflow cells' content into multiple lines
                        'whiteSpace': 'normal',
                        'height': 'auto'
                        },
                    style_header={
                                'backgroundColor': '#0074D9',
                                'color': 'white'
                                },
                    )
            else:
                leave_table = dash_table.DataTable(
                    leave_df.to_dict('records'), 
                    id=id)
            leave_datatable_lst.append(leave_table)
            #print(leave_msg, leave_table)
        return leave_msg, leave_datatable_lst[0], leave_datatable_lst[1]


    # update the leave table after delete        
    @callback(
    [
        Output('leave_table_future', 'data'), 
        ],
    [
        Input('leave_table_future', 'data'),
        ],
    [
        State('url', 'search'),
        State('leave_table_future', 'data_previous'),
        ],
    prevent_initial_call=True,
    )
    def update_leave_data_after_del(data, search, data_previous):
        print('update_leave_data_after_del')
        data_index = set(i['index'] for i in data)
        data_previous_index = set(i['index'] for i in data_previous)
        unmatched_set = data_previous_index.difference(data_index)
        _uuid = dict(parse_qsl(unquote(search))).get('?staff')
        staff = db.db_session.query(db.Staffs).filter(db.Staffs.uuid==_uuid).scalar()
        if data == data_previous:
            raise PreventUpdate
        else:
            if (data != None) and (data_previous != None):
                _del_index = unmatched_set.pop()
                leave = db.db_session.query(db.Leaves).filter(db.Leaves.id == _del_index, db.Leaves.staff_name == staff.staff_name).scalar()
                print(leave)
                if leave:
                    leave_type = leave.type
                    leave_reserved = leave.reserved
                    print(leave)
                    print(leave_type)
                    print(leave_reserved)

                    db.db_session.query(db.Leaves).\
                    filter(db.Leaves.id == _del_index, db.Leaves.staff_name == staff.staff_name).\
                    delete()

                    # update staff quota
                    for k,v in db.leaves_type.items():
                        if leave_type == v['type']:
                            _unit = v['unit']/8
                            _type = k
                            break
                    cur_quota = db.db_session.query(db.Staffs).filter(db.Staffs.staff_name == staff.staff_name).scalar().__dict__.get(_type)
                    print(cur_quota)
                    updated_quota = cur_quota + leave_reserved*_unit
                    print(updated_quota)
                    db.db_session.query(db.Staffs).\
                    filter(db.Staffs.staff_name == staff.staff_name).\
                    update({f"{_type}": updated_quota})
                    
                    db.db_session.commit()
                    return [data]
                else:
                    return [data]


    @callback(
    [
        Output('monthly_all_leave_dataframe', 'data'), 
        ],
    [
        Input('monthly_all_leave_dataframe', 'data'),
        ],
    [
        State('url', 'search'),
        State('monthly_all_leave_dataframe', 'data_previous'),
        ],
    prevent_initial_call=True,
    )
    def update_monthly_all_leave_data_after_del(data, search, data_previous):
        print('update_monthly_all_leave_data_after_del')
        print(data)
        data_index = set(i['id'] for i in data)
        data_previous_index = set(i['id'] for i in data_previous)
        unmatched_set = data_previous_index.difference(data_index)
        if data == data_previous:
            raise PreventUpdate
        else:
            if (data != None) and (data_previous != None):
                _del_index = unmatched_set.pop()
                #print(_del_index)
                for u in data_previous:
                    #print(u)
                    if u.get('id') == _del_index:
                        staff_name = u['staff_name']
                        break
                leave = db.db_session.query(db.Leaves).filter(db.Leaves.id == _del_index, db.Leaves.staff_name == staff_name).scalar()
                print(leave)
                if leave:
                    leave_type = leave.type
                    leave_reserved = leave.reserved
                    print(leave)
                    print(leave_type)
                    print(leave_reserved)

                    db.db_session.query(db.Leaves).\
                    filter(db.Leaves.id == _del_index, db.Leaves.staff_name == staff_name).\
                    delete()

                    # update staff quota
                    for k,v in db.leaves_type.items():
                        if leave_type == v['type']:
                            _unit = v['unit']/8
                            _type = k
                            break
                    cur_quota = db.db_session.query(db.Staffs).filter(db.Staffs.staff_name == staff_name).scalar().__dict__.get(_type)
                    print(cur_quota)
                    updated_quota = cur_quota + leave_reserved*_unit
                    print(updated_quota)
                    db.db_session.query(db.Staffs).\
                    filter(db.Staffs.staff_name == staff_name).\
                    update({f"{_type}": updated_quota})
                    
                    db.db_session.commit()
                    return [data]
                else:
                    return [data]


    # datepicker for check_table
    @callback(
        [
            Output('check_datatable_div', 'children'),
            #Output('agg_check_store', 'data'),
            ],
        [
            Input('check_datepicker', 'start_date'),
            Input('check_datepicker', 'end_date'),
            Input('url', 'search'),
            ],
        )
    def datepicker_check_table(start_date, end_date, search):
        print('datepicker_check_table')
        #print(f'{search} from datepicker_check_table')
        _uuid = dict(parse_qsl(unquote(search))).get('?staff')
        staff = db.db_session.query(db.Staffs).filter(db.Staffs.uuid==_uuid).scalar()
        #print(start_date)
        #print(end_date)
        check_df, required_hours = db.table_generator(start_date, end_date, staff).check_dataframe()
        return [
            check_table(check_df), 
            #check_df.to_json(orient='split', date_format='iso'),
        ]


    # only the last 30 row could be editable
    # match certin string format
    r = re.compile('\d{2}:\d{2}')
    # update the check table         
    @callback(
    [
        Output('change_string', 'children'),
        Output('check_datatable', 'data'),
        Output('check_changes_store', 'data'),
        Output('sum_string', 'children'),
        ],
    [
        Input('check_datatable', 'data'),
        Input('check_button', 'submit_n_clicks'),
        ],
    [
        State('check_datatable', 'data_previous'),
        State('check_datatable', 'active_cell'),
        State('check_revision_reason', 'value'),
        State('url', 'search'),
        State('check_datepicker', 'start_date'),
        State('check_datepicker', 'end_date'),
        State('check_changes_store', 'data'),
        ],
    )
    def update_check_data(data, submit_n_clicks, data_previous, active_cell, reason, search, start_date, end_date, changes):
        _uuid = dict(parse_qsl(unquote(search))).get('?staff')
        staff = db.db_session.query(db.Staffs).filter(db.Staffs.uuid==_uuid).scalar()
        _now = datetime.now()
        print('update_check_data')
        print(active_cell)
        print(ctx.triggered_id)
        if ctx.triggered_id == 'check_datatable':
            if data and data_previous:
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
                                if int(_hour) <= 0 or int(_hour) > 23 or int(_minute) < 0 or int(_minute) > 59:
                                    data[i][col] = None
                            #print(data[i][col])
                        # Restrict Editable time to 31 days
                        if i >= 31:
                            #print(i, data[i][col], data_previous[i][col])
                            data[i][col] = data_previous[i][col]
                    if data[i]['checkin'] != None and data[i]['checkout'] != None:
                        #print(data[i]['checkin'])
                        #print(data[i]['checkout'])
                        # check in <= checkout
                        if datetime_time(int(data[i]['checkin'][0:2]), int(data[i]['checkin'][3:])) >= datetime_time(int(data[i]['checkout'][0:2]), int(data[i]['checkout'][3:])):
                            data[i]['checkin'] = data_previous[i]['checkin']
                            data[i]['checkout'] = data_previous[i]['checkout']
                        # check time > now
                        if datetime.strptime(data[i]['date'], '%m/%d/%Y').date() == _now.date():
                            if datetime_time(int(data[i]['checkin'][0:2]), int(data[i]['checkin'][3:])) > _now.time():
                                data[i]['checkin'] = data_previous[i]['checkin']
                            if datetime_time(int(data[i]['checkout'][0:2]), int(data[i]['checkout'][3:])) > _now.time():
                                data[i]['checkout'] = data_previous[i]['checkout']

                changes = {}
                for i in range(len(data)):
                    if data[i] != data_previous[i]:
                        for col in ('checkin', 'checkout'):
                            if data[i][col] != data_previous[i][col]:
                                current_datetime = data[i]['date'] + ' ' + data[i][col] if data[i][col] != None else None
                                pre_datetime = data_previous[i]['date'] + ' ' + data_previous[i][col] if data_previous[i][col] != None else None
                                changes[i] = {'col':col, 'previous': pre_datetime, 'current': current_datetime}
                print(changes)
                entry = data[active_cell['row']][active_cell['column_id']]
                change_string = f"選擇 {active_cell['column_id']} @ {data[active_cell['row']]['date']}. 修改為 {entry}"
            else:
                change_string = '若要修改打卡紀錄，請提出修改的理由: '
            check_df, required_hours = db.table_generator(start_date, end_date, staff).check_dataframe()
            workhour = round(sum(check_df['worktime[hr]'].iloc[:]),2)
            leavehour = sum(check_df['leave_amount[hr]'].iloc[:])
            sum_string = [html.H5(f"累計工作時數:   {workhour} [hr]"),
                    html.H5(f"累計請假時數     {leavehour} [hr]"), 
                    html.H5(f"須求時數:   {required_hours} [hr]"), 
                    html.H5(f"累計差時:       {round(leavehour + workhour - required_hours,2)} [hr]"),]

            return [change_string, data, changes, sum_string]
        
        elif ctx.triggered_id == 'check_button':
            #print(changes)
            #print(reason)
            #print(active_cell)
            if not submit_n_clicks:
                raise PreventUpdate
            if not reason:
                change_string = f"修改失敗! 請提出您的理由."
            elif not (active_cell and active_cell['column_id'] in ['checkin', 'checkout']):
                change_string = f"修改失敗! 請先選擇一個上班打卡/下班打卡時間格"
            else:
                if not changes:
                    change_string = f"修改失敗! 請填入更改一個上班打卡/下班打卡時間格"
                else:
                    for key, value in changes.items():
                        #print(key, value)
                        col = value['col']
                        if 'checkin' in col:
                            table = db.CheckIn
                        elif 'checkout' in col:
                            table = db.CheckOut
                        pre = datetime.strptime(value['previous'], '%m/%d/%Y %H:%M') if value['previous'] else None
                        cur = datetime.strptime(value['current'], '%m/%d/%Y %H:%M') if value['current'] else None

                        _today_entry = []
                        _entry_date = cur.date() if cur else pre.date()
                        for entry in db.db_session.query(table).filter(table.staff_name == staff.staff_name).all():
                            if entry.created_time.date() == _entry_date:
                                _today_entry.append(entry)
                        _last_entry = _today_entry[-1] if _today_entry else None

                        for entry in _today_entry:
                            if entry != _last_entry:
                                db.db_session.delete(entry)

                        #delete the last entry of the day
                        pre_place = 'None'
                        if _last_entry:
                            pre_place = _last_entry.check_place
                            db.db_session.delete(_last_entry)
                        # insert a row
                        if cur != None:
                            db.db_session.add(table(staff_name=staff.staff_name, created_time=cur, revised=reason, check_place=f'{pre_place} prior' if 'prior' not in pre_place else f'{pre_place}'))
                    db.db_session.commit()
                    #check_table(pd.DataFrame.from_records(data))
                    entry = data[active_cell['row']][active_cell['column_id']]
                    change_string = f"成功修改 {active_cell['column_id']} @ {data[active_cell['row']]['date']}, {entry}"
                changes = {}
                check_df, required_hours = db.table_generator(start_date, end_date, staff).check_dataframe()
                workhour = round(sum(check_df['worktime[hr]'].iloc[:]),2)
                leavehour = sum(check_df['leave_amount[hr]'].iloc[:])
                sum_string = [html.H3(f"累計工作時數:   {workhour} [hr]"),
                        html.H3(f"累計請假時數     {leavehour} [hr]"), 
                        html.H3(f"須球時數:   {required_hours} [hr]"), 
                        html.H3(f"累計差時:       {round(leavehour + workhour - required_hours,2)} [hr]"),]
                return [change_string, check_df.to_dict('records'), changes, sum_string]
    

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
        _uuid = dict(parse_qsl(unquote(search))).get('?staff')
        staff = db.db_session.query(db.Staffs).filter(db.Staffs.uuid==_uuid).scalar() 
        #personal_data_store.data = {'staff':staff}

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
        
        check_h2.children = str(staff.staff_name) + check_type if staff else 'All' + check_type
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
        # You could also return a 404 "URL not found" page here