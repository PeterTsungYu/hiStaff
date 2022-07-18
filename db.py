# Library
from linebot.models import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, inspect, UniqueConstraint, select
from datetime import datetime, date, timedelta
import numpy as np
import pandas as pd
import os
from dotenv import load_dotenv
def strptime(time):
    if 't' in time:
        return datetime.strptime(time[2:], '%y-%m-%dt%H:%M')
    else:
        return datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
def strf_datetime(dt):
    date_args = [u for i in dt.split(',') for u in i.split(' ') if all([u != cond for cond in ['','PM','AM']])]
    #config.logger.debug(date_args)
    time_args = date_args[-1].split(':')
    #config.logger.debug(time_args)
    return str(datetime(
                year=int(date_args[2]), month=int(datetime.strptime(date_args[0], "%b").month), day=int(date_args[1]), 
                hour=int(time_args[0]), minute=int(time_args[1]), second=int(time_args[2]))
                )
#from collections import namedtuple
#start_end = namedtuple('start_end', ['start', 'end'])

# Custom                
import config
from hicalendar import hiCalendar


engine = create_engine(config.db_path, convert_unicode=True)
#print(engine)

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=True, bind=engine))
#print(db_session())
#print(db_session)
# When True, all query operations will issue a Session.flush() call to this Session before proceeding
# It’s typical that autoflush is used in conjunction with autocommit=False
# The Session object features autobegin the tx state, so that normally it is not necessary to call the Session.begin() method explicitly.

Base = declarative_base()
Base.query = db_session.query_property()


def get_or_create_user(user_id):
    user = Users.query.filter_by(id=user_id).first()
    #print(f'{user} in db')
    
    if not user:
        profile = config.line_bot_api.get_profile(user_id)
        # insert entries into the database
        user = Users(id=user_id, nick_name=profile.display_name, image_url=profile.picture_url)
        db_session.add(user) # insert query
        db_session.commit()
        #print(f"Add {user} to db")
    return user

class Users(Base):
    __tablename__ = 'users_table'
    id = Column(String, primary_key=True)
    nick_name = Column(String)
    image_url = Column(String(length=256))
    created_time = Column(DateTime, default=datetime.now())
    
    def __repr__(self):
        return f'<User {self.nick_name!r}>'

class CheckIn(Base):
    __tablename__ = 'checkin_table'
    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_name = Column(String, ForeignKey('staffs_table.staff_name'))
    created_time = Column(DateTime, default=datetime.now())
    check_place = Column(String, default='None')
    
    def __repr__(self):
        return f'<CheckIn {self.id!r}>'

class CheckOut(Base):
    __tablename__ = 'checkout_table'
    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_name = Column(String, ForeignKey('staffs_table.staff_name'))
    created_time = Column(DateTime, default=datetime.now())
    check_place = Column(String, default='None')
    def __repr__(self):
        return f'<CheckOut {self.id!r}>'


class Leaves(Base):
    __tablename__ = 'leaves_table'
    now = datetime.now()
    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_name = Column(String, ForeignKey('staffs_table.staff_name'), nullable=False)
    type = Column(String, nullable=False)
    start = Column(DateTime)
    end = Column(DateTime) 
    reserved = Column(Integer)
    def __repr__(self):
        return f'<Leave {self.id!r}>'

leaves_type = {
        'Official_Leave':{'type':'OF', 'unit':2}, #[hr]
        'Personal_Leave':{'type':'PS', 'unit':2}, #[hr]
        'Sick_Leave':{'type':'SK', 'unit':4}, #[hr]
        'Business_Leave':{'type':'BN', 'unit':2}, #[hr]
        'Deferred_Leave':{'type':'DF', 'unit':4}, #[hr]
        'Annual_Leave':{'type':'AA', 'unit':4}, #[hr]
        'Funeral_Leave':{'type':'FN', 'unit':4}, #[hr]
        'Menstruation_Leave':{'type':'MS', 'unit':8}, #[hr]
        'Marital_Leave':{'type':'MT', 'unit':8}, #[hr]
        'Maternity_Leave':{'type':'MN', 'unit':8}, #[hr]
        'Paternity_Leave':{'type':'PT', 'unit':8}, #[hr]
    }
    
class Staffs(Base):
    __tablename__ = 'staffs_table'
    uuid = Column(String, primary_key=True)
    staff_name = Column(String, nullable=False)
    Official_Leave = Column(Float, default=365)
    Personal_Leave = Column(Float, default=14)
    Sick_Leave = Column(Float, default=30)
    Business_Leave = Column(Float, default=365)
    Deferred_Leave = Column(Float, default=0)
    Annual_Leave = Column(Float, default=10)
    Funeral_Leave = Column(Float, default=8)
    Menstruation_Leave = Column(Float, default=12)
    Marital_Leave = Column(Float, default=8)
    Maternity_Leave = Column(Float, default=40)
    Paternity_Leave = Column(Float, default=5)
    '''
    def __repr__(self):
        return f'<Staff {self.staff_name!r}>'
    '''

Staffs.checkin_time = relationship("CheckIn", backref="many_staff")
Staffs.checkout_time = relationship("CheckOut", backref="many_staff")
Staffs.Leaves_time = relationship("Leaves", backref="many_staff")

def get_Staff_profile_lst():
    # staff list and uuid
    Staff_profile_checklst = [ #temp lst for checking uuid
        Staffs(staff_name='Peter', Annual_Leave=10),
        Staffs(staff_name='Nina'),
        Staffs(staff_name='Ethan'),
        Staffs(staff_name='Marvin'),
        Staffs(staff_name='Johnson'),
        ]

    Staff_profile_lst = [] # finalize lst with valid uuid
    for i in range(len(Staff_profile_checklst)): 
        if not os.environ.get(Staff_profile_checklst[i].staff_name):
            continue
        else:
            Staff_profile_checklst[i].uuid = os.environ.get(Staff_profile_checklst[i].staff_name) 
            Staff_profile_lst.append(Staff_profile_checklst[i])
    return Staff_profile_lst


def init_staffs_table():
    print(db_session())
    Staff_profile_lst = get_Staff_profile_lst()
    print(Staff_profile_lst)

    if inspect(engine).has_table('staffs_table'):
        db_session.query(Staffs).delete()
    #Base.metadata.create_all(bind=engine)
    db_session.add_all(Staff_profile_lst) # a way to insert many query
    db_session.commit()
    #db_session.remove()
    config.logger.debug('Initialized Staff table')
    #config.logger.debug(db_session.query(Staffs).all())


def update_staffs_table():
    print(db_session())
    Staff_profile_lst = get_Staff_profile_lst()
    print(Staff_profile_lst)

    if inspect(engine).has_table('staffs_table'):
        _staff_lst = db_session.query(Staffs).all()
        _lst_profile = [i.staff_name for i in Staff_profile_lst]
        _lst_db = [i.staff_name for i in _staff_lst]

        for i in Staff_profile_lst:
            if i.staff_name not in _lst_db:
                db_session.add(i)
                config.logger.debug(f'add {i.staff_name}')
        for i in _staff_lst:
            if i.staff_name not in _lst_profile:
                db_session.delete(i)
                config.logger.debug(f'del {i.staff_name}')
        #db_session.query(Staffs).delete()
        #db_session.add_all(Staff_profile_lst) # a way to insert many query
    else:
        db_session.add_all(Staff_profile_lst)
        #Base.metadata.create_all(bind=engine)
    db_session.commit()
    #db_session.remove()
    config.logger.debug('Staff table is up to date')
    #config.logger.debug(db_session.query(Staffs).all())


class staffs_datatable_generator:
    def __init__(self, staff):
        self.staff=staff

    def staffs_datatable(self):
        df_quota = pd.DataFrame([( k, v['unit'], dict(self.staff.__dict__.items()).get(k)) for k,v in leaves_type.items()], columns=['Type', 'Unit[hr]', 'Quota[day]'])
        return df_quota


def check_leave_calc(staff, start, end, date_index):
    location_dict = {}
    in_dict = {}
    for i in staff.checkin_time:
        if start <= i.created_time.date() <= end: 
            in_dict[i.created_time.date()]=i.created_time
            location_dict[i.created_time.date()] = {}
            location_dict[i.created_time.date()]['in'] = i.check_place
    in_lst = [f"{str(in_dict[i].hour).zfill(2)}:{str(in_dict[i].minute).zfill(2)}" if i in in_dict.keys() else None for i in date_index]

    out_dict = {}
    for i in staff.checkout_time:
        if start <= i.created_time.date() <= end: 
            out_dict[i.created_time.date()]=i.created_time
            if isinstance(location_dict.get(i.created_time.date()), dict):
                location_dict[i.created_time.date()]['out'] = i.check_place
            else:
                location_dict[i.created_time.date()] = {}
                location_dict[i.created_time.date()]['out'] = i.check_place
    out_lst = [f"{str(out_dict[i].hour).zfill(2)}:{str(out_dict[i].minute).zfill(2)}" if i in out_dict.keys() else None for i in date_index]

    location_lst = [f"{location_dict[i].get('in')} {location_dict[i].get('out')}" if i in location_dict.keys() else None for i in date_index]
    
    leave_dict = {}
    leave_lst_dict = {}
    for i in staff.Leaves_time:
        if start <= i.start.date() <= end: 
            for k,v in leaves_type.items():
                if i.type == v['type']:
                    leave_type = k
                    # unit within a day
                    if leave_type not in ['Menstruation_Leave', 'Marital_Leave', 'Maternity_Leave', 'Paternity_Leave']:
                        leave_amount = v['unit'] * int(i.reserved)
                        if not leave_lst_dict.get(i.start.date()):
                            leave_dict[i.start.date()] = {'leave_start': f'{leave_type}\n{i.start.time()}_{leave_amount}[hr]', 'leave_amount': leave_amount} 
                            leave_lst_dict[i.start.date()] = {'start': [i.start], 'end': [i.end]}  
                        else: 
                            leave_dict[i.start.date()]['leave_start'] = f'{leave_dict[i.start.date()]["leave_start"]}\n{leave_type}\n{i.start.time()}_{leave_amount}[hr]'
                            leave_dict[i.start.date()]['leave_amount'] = leave_dict[i.start.date()]["leave_amount"]+leave_amount
                            leave_lst_dict[i.start.date()]['start'].append(i.start)
                            leave_lst_dict[i.start.date()]['end'].append(i.end)
                    # unit across a day
                    else:
                        leave_amount = int(i.reserved)
                        for u in pd.date_range(i.start.date(), i.end.date()): #pd.date_range include the start and end
                            if start <= u <= end:
                                if u.date() == i.start.date():
                                    if not leave_dict.get(u.date()):
                                        leave_dict[u.date()] = {'leave_start': f'{leave_type}\n{i.start.time()}_{v["unit"]}[hr]', 'leave_amount': v['unit']}
                                        leave_lst_dict[u.date()] = {'start': [i.start], 'end': [i.start+timedelta(hours=v['unit'])]}
                                    else:
                                        leave_dict[u.date()]['leave_start'] = f'{leave_dict[u.date()]["leave_start"]}\n{leave_type}\n{i.start.time()}_{v["unit"]}[hr]'
                                        leave_dict[u.date()]['leave_amount'] = leave_dict[u.date()]["leave_amount"]+v['unit']
                                        leave_lst_dict[u.date()]['start'].append(i.start)
                                        leave_lst_dict[i.start.date()]['end'].append(i.start+timedelta(hours=v['unit']))
                                else:
                                    if not leave_dict.get(u.date()):
                                        leave_dict[u.date()] = {'leave_start': f'{leave_type}\n{(u+timedelta(hours=8)+timedelta(minutes=30)).time()}_{v["unit"]}[hr]', 'leave_amount': v['unit']}  
                                        leave_lst_dict[u.date()] = {'start': [u+timedelta(hours=8)+timedelta(minutes=30)], 'end': [u+timedelta(hours=17)+timedelta(minutes=30)]} 
                                    else: 
                                        leave_dict[u.date()]['leave_start'] = f'{leave_dict[u.date()]["leave_start"]}\n{leave_type}\n{(u+timedelta(hours=8)+timedelta(minutes=30)).time()}_{v["unit"]}[hr]'
                                        leave_dict[u.date()]['leave_amount'] = leave_dict[u.date()]["leave_amount"]+v['unit']
                                        leave_lst_dict[u.date()]['start'].append(u+timedelta(hours=8)+timedelta(minutes=30))
                                        leave_lst_dict[u.date()]['end'].append(u+timedelta(hours=17)+timedelta(minutes=30))
                    break
    print(leave_dict)
    leave_time_lst = [leave_dict[i]['leave_start'] if i in leave_dict.keys() else None for i in date_index]
    #print(leave_time_lst)
    leave_amount_lst = [leave_dict[i]['leave_amount'] if i in leave_dict.keys() else 0 for i in date_index]
    #print(leave_amount_lst)

    worktime_dict = {}
    for i in date_index:
        overlap = 0
        if (in_dict.get(i) != None) and (out_dict.get(i) != None):
            if leave_lst_dict.get(i):
                for u in range(len(leave_lst_dict[i]['start'])):
                    latest_start = max(in_dict[i], leave_lst_dict[i]['start'][u])
                    earliest_end = min(out_dict[i], leave_lst_dict[i]['end'][u])
                    delta = round((earliest_end - latest_start).total_seconds()/60/60,2)
                    overlap += max(0, delta)
                worktime_dict[i] = (out_dict[i].timestamp() - in_dict[i].timestamp())/60/60 - overlap
            else:
                worktime_dict[i] = (out_dict[i].timestamp() - in_dict[i].timestamp())/60/60
    worktime_lst = [round(worktime_dict[i],2) if i in worktime_dict.keys() else 0 for i in date_index]

    return in_lst, out_lst, location_lst, leave_time_lst, leave_amount_lst, worktime_lst

class season_table_generator:
    def __init__(self, staff, year, season):
        self.season = season
        self.staff = staff
        if staff == 'All':
            self.staff_lst = db_session.query(Staffs)
        else:
            self.staff_lst = [staff]
        self.staff_name_lst = [staff.staff_name for staff in self.staff_lst]
        season_dict = {'Q1':[1,2,3], 'Q2':[4,5,6], 'Q3':[7,8,9], 'Q4':[10,11,12]}
        self.month_lst = season_dict[season]
        self.calendar_lst=[
            hiCalendar(start = datetime(year, season_dict[season][0], 1), end = (datetime(year, season_dict[season][0], 1) + pd.offsets.MonthEnd(1)).date()),
            hiCalendar(start = datetime(year, season_dict[season][1], 1), end = (datetime(year, season_dict[season][1], 1) + pd.offsets.MonthEnd(1)).date()),
            hiCalendar(start = datetime(year, season_dict[season][2], 1), end = (datetime(year, season_dict[season][2], 1) + pd.offsets.MonthEnd(1)).date()),
        ]
    def check_dataframe(self):
        _season = 0
        seasonal_lst = []
        df_lst = []
        for calendar in self.calendar_lst:
            start = calendar.start.date()
            end = calendar.end
            date_index = calendar.date_index.date
            momthly_lst = {}
            for staff in self.staff_lst:
                in_lst, out_lst, location_lst, leave_time_lst, leave_amount_lst, worktime_lst = check_leave_calc(staff, start, end, date_index)
                
                work_amount = round(sum(worktime_lst), 2)
                leave_amount = round(sum(leave_amount_lst), 2)
                required_amount = calendar.bdays_count().sum()*9
                diff = (work_amount + leave_amount) - required_amount
                momthly_lst[staff.staff_name] = (work_amount, leave_amount, required_amount, diff)
            monthly_df = pd.DataFrame(data={i: momthly_lst[i] for i in self.staff_name_lst}, index=('work_amount[hr]', 'leave_amount[hr]', 'required_amount[hr]', 'diff[hr]')).rename_axis(f'month_{self.month_lst[_season]}').reset_index()
            df_lst.append(monthly_df)
            _season += 1
            #print(monthly_df)
            seasonal_lst.append(momthly_lst)

        #print(df_lst)
        #print(seasonal_lst)
        _seasonal_dict_temp = {} 
        for i in seasonal_lst:
            for k,v in i.items():
                if not _seasonal_dict_temp.get(k):
                    _seasonal_dict_temp[k] = []    
                _seasonal_dict_temp[k].append(v)
        _seasonal_dict = {}
        for k,v in _seasonal_dict_temp.items():
            _seasonal_dict[k] = np.array(v).sum(axis=0)
        seasonal_df = pd.DataFrame(data=_seasonal_dict, index=('Total_work_amount[hr]', 'Total_leave_amount[hr]', 'Total_required_amount[hr]', 'Total_diff[hr]')).rename_axis(f'Seasonal Summary').reset_index()
        #print(seasonal_df)
        df_lst.append(seasonal_df)

        return df_lst


class all_table_generator:
    def __init__(self, year, month):
        self.calendar=hiCalendar(start = datetime(year, month, 1), end = (datetime(year, month, 1) + pd.offsets.MonthEnd(1)).date())
        self.staff_lst = db_session.query(Staffs)
    
    def check_dataframe(self):
        all_check_lst = []
        start = self.calendar.start.date()
        end = self.calendar.end
        date_index = self.calendar.date_index.date

        for staff in self.staff_lst:
            in_lst, out_lst, location_lst, leave_time_lst, leave_amount_lst, worktime_lst = check_leave_calc(staff, start, end, date_index)

            work_amount = round(sum(worktime_lst), 2)
            leave_amount = round(sum(leave_amount_lst), 2)
            required_amount = self.calendar.bdays_count().sum()*9
            diff = (work_amount + leave_amount) - required_amount

            in_out_lst = [f'{in_lst[i]} {out_lst[i]} \n{leave_time_lst[i]}' for i in range(len(date_index))]
            df = pd.DataFrame(data={f'{staff.staff_name}':in_out_lst})
            #print(df)

            df = pd.concat([pd.DataFrame([work_amount, leave_amount, required_amount, diff], columns=df.columns), df], ignore_index=True)
            all_check_lst.append(df)
        date_index = ['work_amount[hr]', 'leave_amount[hr]', 'required_amount[hr]', 'diff[hr]'] + [str(i) for i in date_index]
        df_all = pd.concat([pd.DataFrame(data={'date':date_index})] + all_check_lst, axis=1)
        
        return df_all

    def update_deferred_leave(self):
        print(db_session)
        try:
            month_all_df = self.check_dataframe()
            month_all_dict = month_all_df[month_all_df['date']=='diff[hr]'].to_dict('records')[0]
            for staff in self.staff_lst:
                #print(month_all_dict)
                deferred_delta = month_all_dict.get(staff.staff_name)
                # update staff.Deferred_Leave
                cur_quota = db_session.query(Staffs).filter(Staffs.staff_name == staff.staff_name).scalar().__dict__.get('Deferred_Leave')
                #print(cur_quota)
                updated_quota = cur_quota + deferred_delta
                #print(updated_quota)
                db_session.query(Staffs).\
                filter(Staffs.staff_name == staff.staff_name).\
                update({"Deferred_Leave": updated_quota})
                db_session.commit()
            return 'successful update_deferred_leave'
        except BaseException as e:
            return str(e)
        finally:
            db_session.close()


class table_generator:
    def __init__(self, start, end, staff):
        self.start = start
        self.end = end
        self.calendar=hiCalendar(start, end)
        self.staff=staff

    def gen_table(self, table_cls):
        df = pd.read_sql(
            sql = db_session.query(table_cls).filter(table_cls.staff_name==self.staff.staff_name).statement,
            con = engine
        )
        return df
    
    def leave_dataframe(self):
        leave_dict = {}
        for i in self.staff.Leaves_time:
            if self.start <= i.start.date() <= self.end: 
                for k,v in leaves_type.items():
                    if i.type == v['type']:
                        leave_type = k
                        leave_unit = v['unit']
                leave_dict[f'{i.id}'] = [leave_type, i.start, i.end, i.reserved, leave_unit]
        if leave_dict:
            leave_df = pd.DataFrame.from_dict(leave_dict, orient='index', columns=['type', 'start', 'end', 'reserved', 'unit'])[::-1].reset_index()
            leave_df['start'] = leave_df['start'].dt.strftime("%m/%d/%Y, %A\n%H:%M:%S")
            leave_df['end'] = leave_df['end'].dt.strftime("%m/%d/%Y, %A\n%H:%M:%S")
            #datetime. strptime(date_time_str, '%d/%m/%y %H:%M:%S')
            #df = pd.DataFrame(data={'date':bdays_hdays_df.index, 'weekday': bdays_hdays_df.weekday,'checkin':in_lst, 'checkout':out_lst, 'worktime[hr]':worktime_lst, 'aggregation[hr]':agg_lst})
            print(leave_df)
        else:
            leave_df = pd.DataFrame()
        return leave_df

    def check_dataframe(self):
        start = datetime.strptime(self.start, '%Y-%m-%d').date()
        end = datetime.strptime(self.end, '%Y-%m-%d').date()
        date_index = self.calendar.date_index.date
        bdays_hdays_df = self.calendar.bdays_hdays()

        in_lst, out_lst, location_lst, leave_time_lst, leave_amount_lst, worktime_lst = check_leave_calc(self.staff, start, end, date_index)
        
        agg_lst = [round(sum(worktime_lst[:i+1]) + sum(leave_amount_lst[:i+1]), 2) for i in range(len(worktime_lst))]
        #print(agg_lst)

        df = pd.DataFrame(data={'date':bdays_hdays_df.index, 'weekday': bdays_hdays_df.weekday,'checkin':in_lst, 'checkout':out_lst, 'location':location_lst, 'worktime[hr]':worktime_lst, 'leave_start':leave_time_lst, 'leave_amount[hr]':leave_amount_lst, 'aggregation[hr]':agg_lst})
        df['date'] = df['date'].dt.strftime("%m/%d/%Y")
        df.iloc[:] = df.iloc[::-1].values # reverse rows

        required_hours = self.calendar.bdays_count().sum()*9
        
        #print(df, required_hours)
        return df, required_hours

##======================line_msg==================================
def location_bubble(check: str, staff_name: str, location='Location'):
    '''
    check: 'checkin' or 'checkout'
    '''
    bubble = BubbleContainer(
                direction='ltr',
                body=BoxComponent(
                    layout='vertical',
                    spacing='sm',
                    contents=[
                        TextComponent(
                            text=f"{check} {staff_name}\nLocation: {location}",
                            weight='bold',
                            size='xl',
                            wrap=True,
                            contents=[]
                        ),
                    ]
                ),
                footer=BoxComponent(
                    layout='vertical',
                    spacing='sm',
                    contents=[
                        ButtonComponent(
                            style='primary',
                            action=PostbackAction(
                                label="Revise Location",
                                data=f'id=1&staff_name={staff_name}&check={check}',
                            )
                        ),
                        ButtonComponent(
                            style='primary',
                            action=PostbackAction(
                                label="Proceed to next",
                                data=f'id=2&staff_name={staff_name}&check={check}&location={location}',
                            )
                        )
                    ]
                )
            )
    return FlexSendMessage(alt_text=f'Hi {staff_name}, {check} yourself!', contents=bubble)


def moment_bubble(check: str, img_url: str, staff_name: str, now: str, moment='Pls Select Date/Time', location='Location'):
    print((now - pd.offsets.DateOffset(minutes=30)).strftime("%Y-%m-%dT%H:%M"))
    '''
    check: 'checkin' or 'checkout' or 'take a leave'
    '''
    if check == 'checkin':
        datetimepicker = DatetimePickerAction(
                            label="moment",
                            data=f'id=3&staff_name={staff_name}&check={check}&location={location}',
                            mode='datetime',
                            initial=now.strftime("%Y-%m-%dT%H:%M"),
                            max = now.strftime("%Y-%m-%dT")+'23:59',
                            min = (now - pd.offsets.DateOffset(minutes=30)).strftime("%Y-%m-%dT%H:%M")
                            )
    elif check == 'checkout':
        datetimepicker = DatetimePickerAction(
                            label="moment",
                            data=f'id=3&staff_name={staff_name}&check={check}&location={location}',
                            mode='datetime',
                            initial=now.strftime("%Y-%m-%dT%H:%M"),
                            min = now.strftime("%Y-%m-%dT")+'00:00',
                            max = now.strftime("%Y-%m-%dT%H:%M"),
                            )
    elif '_Leave' in check :
        datetimepicker = DatetimePickerAction(
                            label="moment",
                            data=f'id=3&staff_name={staff_name}&check={check}&location={location}',
                            mode='datetime',
                            initial=now.strftime("%Y-%m-%dT%H:%M"),
                            min = (now - pd.offsets.DateOffset(minutes=30)).strftime("%Y-%m-%dT%H:%M")
                            )
    else:
        pass

    bubble = BubbleContainer(
                hero=ImageComponent(
                size="full",
                aspect_ratio="20:13",
                aspect_mode="cover",
                url=img_url,
                ),
                body=BoxComponent(
                    layout="vertical",
                    spacing="sm",
                    contents=[
                        TextComponent(
                            text=staff_name,
                            wrap=True,
                            weight="bold",
                            size="xl"),
                        BoxComponent(
                            layout="baseline",
                            contents=[
                                TextComponent(
                                    text=f'{check}',
                                    wrap=True,
                                    weight='bold',
                                    size= "xl",
                                    flex=0
                                )
                            ]
                        ),
                        TextComponent(
                            margin='md',
                            text=f"{check}\nLocation: {location}\nDateTime: {moment}",
                            wrap=True,
                            size='xs',
                            color='#aaaaaa'
                        )
                    ]
                ),
                footer=BoxComponent(
                    layout="vertical",
                    spacing="sm",
                    contents=[
                        ButtonComponent(
                            style="primary",
                            color='#1DB446',
                            action=datetimepicker
                        ),
                    ]
                )
            )
    return FlexSendMessage(alt_text=f'Hi {staff_name}, Clock!', contents=bubble)

def check_bubble(check: str, staff_name: str, moment='Pls Select Date/Time', location='Location'):
    bubble = BubbleContainer(
                direction='ltr',
                body=BoxComponent(
                    layout='vertical',
                    spacing='sm',
                    contents=[
                        TextComponent(
                            text=f"{check} {staff_name}\nLocation: {location}\nDateTime: {moment}",
                            weight='bold',
                            size='xl',
                            wrap=True,
                            contents=[]
                        ),
                    ]
                ),
                footer=BoxComponent(
                    layout='vertical',
                    spacing='sm',
                    contents=[
                        ButtonComponent(
                            style='primary',
                            action=PostbackAction(
                                label="Revise DateTime",
                                data=f'id=2&staff_name={staff_name}&check={check}&location={location}',
                            )
                        ),
                        ButtonComponent(
                            style='primary',
                            action=PostbackAction(
                                label="That's it",
                                data=f'id=4&staff_name={staff_name}&check={check}&moment={moment}&location={location}',
                            )
                        )
                    ]
                )
            )
    return FlexSendMessage(alt_text=f'Hi {staff_name}, {check} yourself!', contents=bubble)

def reply_dash_msg():
    pass

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    get_Staff_profile_lst()
    init_staffs_table()
    update_staffs_table()
    #season_table_generator(year=2022, season='Q1').check_dataframe()
    #table_generator(start=datetime.now(), end=datetime.now(), staff_name='謝宗佑').check_dataframe()
    df = all_table_generator(year=2022, month=7).check_dataframe()
    print(df[df['date']=='diff[hr]'].to_dict('records'))
    #print(Base.metadata)
    print(db_session())
    db_session.remove()