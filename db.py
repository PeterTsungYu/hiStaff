# Library
from linebot.models import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, inspect, UniqueConstraint, select
from datetime import datetime, date
import numpy as np
import pandas as pd
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

# Custom                
import config
from hicalendar import hiCalendar


engine = create_engine(config.db_path, convert_unicode=True)
#print(engine)

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=True, bind=engine))
# When True, all query operations will issue a Session.flush() call to this Session before proceeding
# It’s typical that autoflush is used in conjunction with autocommit=False
# The Session object features autobegin the tx state, so that normally it is not necessary to call the Session.begin() method explicitly.

Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    #config.logger.info(inspect(engine).has_table('staffs_table'))
    if inspect(engine).has_table('staffs_table'):
        _staff_lst = db_session.query(Staffs).order_by(Staffs.id).all()

        if len(staff_lst) == len(_staff_lst):
            for i in range(len(staff_lst)):
                if staff_lst[i].staff_name != _staff_lst[i].staff_name:
                    db_session.query(Staffs).delete()
                    db_session.add_all(staff_lst) # a way to insert many query
                    break
        else:
            print(2)
            db_session.query(Staffs).delete()
            db_session.add_all(staff_lst) # a way to insert many query
        
    else:
        Base.metadata.create_all(bind=engine)
        db_session.add_all(staff_lst)
    db_session.commit()
    #config.logger.debug(db_session.query(Staffs).all())


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
    
    def __repr__(self):
        return f'<CheckIn {self.id!r}>'

class CheckOut(Base):
    __tablename__ = 'checkout_table'
    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_name = Column(String, ForeignKey('staffs_table.staff_name'))
    created_time = Column(DateTime, default=datetime.now())
    def __repr__(self):
        return f'<CheckOut {self.id!r}>'


class Personal_Leave(Base):
    __tablename__ = 'Personal_Leave_table'
    now = datetime.now()
    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_name = Column(String, ForeignKey('staffs_table.staff_name'))
    start = Column(DateTime, default=now)
    end = Column(DateTime, default=now)
    def __repr__(self):
        return f'<Personal_Leave {self.id!r}>'


class Sick_Leave(Base):
    __tablename__ = 'Sick_Leave_table'
    now = datetime.now()
    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_name = Column(String, ForeignKey('staffs_table.staff_name'))
    start = Column(DateTime, default=now)
    end = Column(DateTime, default=now)
    def __repr__(self):
        return f'<Sick_Leave {self.id!r}>'

class Business_Leave(Base):
    __tablename__ = 'Business_Leave_table'
    now = datetime.now()
    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_name = Column(String, ForeignKey('staffs_table.staff_name'))
    start = Column(DateTime, default=now)
    end = Column(DateTime, default=now)
    def __repr__(self):
        return f'<Business_Leave {self.id!r}>'

class Deferred_Leave(Base):
    __tablename__ = 'Deferred_Leave_table'
    now = datetime.now()
    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_name = Column(String, ForeignKey('staffs_table.staff_name'))
    start = Column(DateTime, default=now)
    end = Column(DateTime, default=now)
    def __repr__(self):
        return f'<Deferred_Leave {self.id!r}>'

class Annual_Leave(Base):
    __tablename__ = 'Annual_Leave_table'
    now = datetime.now()
    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_name = Column(String, ForeignKey('staffs_table.staff_name'))
    start = Column(DateTime, default=now)
    end = Column(DateTime, default=now)
    def __repr__(self):
        return f'<Annual_Leave {self.id!r}>'

class Marital_Leave(Base):
    __tablename__ = 'Marital_Leave_table'
    now = datetime.now()
    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_name = Column(String, ForeignKey('staffs_table.staff_name'))
    start = Column(DateTime, default=now)
    end = Column(DateTime, default=now)
    def __repr__(self):
        return f'<Marital_Leave {self.id!r}>'

class Maternity_Leave(Base):
    __tablename__ = 'Maternity_Leave_table'
    now = datetime.now()
    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_name = Column(String, ForeignKey('staffs_table.staff_name'))
    start = Column(DateTime, default=now)
    end = Column(DateTime, default=now)
    def __repr__(self):
        return f'<Maternity_Leave {self.id!r}>'

class Staffs(Base):
    __tablename__ = 'staffs_table'
    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_name = Column(String)
    Personal_Leave = Column(Float, default=0)
    Sick_Leave = Column(Float, default=0)
    Business_Leave = Column(Float, default=0)
    Deffered_Leave = Column(Float, default=0)
    Annual_Leave = Column(Float, default=10.0)
    Marital_Leave = Column(Float, default=7.0)
    Maternity_Leave = Column(Float, default=7.0)
    def __repr__(self):
        return f'<Staff {self.staff_name!r}>'

Staffs.checkin_time = relationship("CheckIn", backref="many_staff")
Staffs.checkout_time = relationship("CheckOut", backref="many_staff")
Staffs.Personal_Leave_time = relationship("Personal_Leave", backref="many_staff")
Staffs.Sick_Leave_time = relationship("Sick_Leave", backref="many_staff")
Staffs.Business_Leave_time = relationship("Business_Leave", backref="many_staff")
Staffs.Deferred_Leave_time = relationship("Deferred_Leave", backref="many_staff")
Staffs.Annual_Leave_time = relationship("Annual_Leave", backref="many_staff")
Staffs.Marital_Leave_time = relationship("Marital_Leave", backref="many_staff")
Staffs.Maternity_Leave_time = relationship("Maternity_Leave", backref="many_staff")

staff_lst = [
    Staffs(staff_name='謝宗佑', Annual_Leave=10),
    Staffs(staff_name='佳嶸'),
    #Staffs(staff_name='Jessie'),
    ]

class season_table_generator:
    def __init__(self, staff_name, year, season):
        self.staff_name=staff_name
        if staff_name == 'all':
            self.staff_lst = db_session.query(Staffs)
        else:
            self.staff_lst = [db_session.query(Staffs).filter(Staffs.staff_name==staff_name).scalar()]
        self.staff_name_lst = [staff.staff_name for staff in self.staff_lst]
        season_dict = {'Q1':[1,2,3], 'Q2':[4,5,6], 'Q3':[7,8,9], 'Q4':[10,11,12]}
        self.season = season_dict[season]
        self.calendar_lst=[
            hiCalendar(start = datetime(year, season_dict[season][0], 1), end = (datetime(year, season_dict[season][0], 1) + pd.offsets.MonthEnd(1)).date()),
            hiCalendar(start = datetime(year, season_dict[season][1], 1), end = (datetime(year, season_dict[season][1], 1) + pd.offsets.MonthEnd(1)).date()),
            hiCalendar(start = datetime(year, season_dict[season][2], 1), end = (datetime(year, season_dict[season][2], 1) + pd.offsets.MonthEnd(1)).date()),
        ]
    def check_dataframe(self):
        seasonal_required_hours = 0
        check_lst_2d = []
        for calendar in self.calendar_lst:
            date_index = calendar.date_index.date
            check_lst_1d = []
            for staff in self.staff_lst:
                out_dict = {}
                for i in staff.checkout_time:
                    out_dict[i.created_time.date()]=i.created_time

                in_dict = {}
                for i in staff.checkin_time:
                    in_dict[i.created_time.date()]=i.created_time
                
                worktime_dict = {}
                for i in date_index:
                    if (in_dict.get(i) != None) and (out_dict.get(i) != None):
                        worktime_dict[i] = (out_dict[i].timestamp() - in_dict[i].timestamp())/60/60
                worktime_lst = [round(worktime_dict[i],2) if i in worktime_dict.keys() else 0 for i in date_index]
                agg_lst = [round(sum(worktime_lst[:i+1]),2) for i in range(len(worktime_lst))]
                check_lst_1d.append(agg_lst[-1])
            check_lst_2d.append(check_lst_1d)
            seasonal_required_hours += ((calendar.bdays_bool_df() * 9).sum()[0])
        #print(np.array(check_lst_2d).sum(axis=0))
        monthly_df = pd.DataFrame(np.array(check_lst_2d), columns=self.staff_name_lst)
        total_df = pd.DataFrame([np.array(check_lst_2d).sum(axis=0)], columns=self.staff_name_lst)
        diff_df = pd.DataFrame([np.array(check_lst_2d).sum(axis=0) - seasonal_required_hours], columns=self.staff_name_lst)
        df = pd.concat([monthly_df, total_df, diff_df], axis=0, ignore_index=True)
        #print(total_df)
        #print(diff_df)
        #print(df)
        date_index = self.season + ['agg [hr]', 'diff [hr]']
        df = pd.concat([pd.DataFrame(data={'index':date_index}), df], axis=1)

        return df


class all_table_generator:
    def __init__(self, year, month):
        self.calendar=hiCalendar(start = datetime(year, month, 1), end = (datetime(year, month, 1) + pd.offsets.MonthEnd(1)).date())
        self.staff_lst = db_session.query(Staffs)
    def check_dataframe(self):
        check_lst = []
        date_index = self.calendar.date_index.date
        for staff in self.staff_lst:
            out_dict = {}
            for i in staff.checkout_time:
                out_dict[i.created_time.date()]=i.created_time
            out_lst = [out_dict[i].time() if i in out_dict.keys() else None for i in date_index]

            in_dict = {}
            for i in staff.checkin_time:
                in_dict[i.created_time.date()]=i.created_time
            in_lst = [in_dict[i].time() if i in in_dict.keys() else None for i in date_index]
            
            worktime_dict = {}
            for i in date_index:
                if (in_dict.get(i) != None) and (out_dict.get(i) != None):
                    worktime_dict[i] = (out_dict[i].timestamp() - in_dict[i].timestamp())/60/60
            worktime_lst = [round(worktime_dict[i],2) if i in worktime_dict.keys() else 0 for i in date_index]
            agg_lst = [round(sum(worktime_lst[:i+1]),2) for i in range(len(worktime_lst))]
            #print(agg_lst)

            in_out_lst = [f'{in_lst[i]} {out_lst[i]}'  for i in range(len(date_index))]
            df = pd.DataFrame(data={f'{staff.staff_name}':in_out_lst})
            #print(df)
            
            required_hours = (self.calendar.bdays_bool_df() * 9).sum()[0]

            if agg_lst != []:
                df = pd.concat([pd.DataFrame([agg_lst[-1], (agg_lst[-1]-required_hours)], columns=df.columns), df], ignore_index=True)
            else:
                df = pd.concat([pd.DataFrame([0, 0], columns=df.columns), df], ignore_index=True)
            check_lst.append(df)
        date_index = ['aggregation[hr]', 'diff[hr]'] + [str(i) for i in date_index]
        df_all = pd.concat([pd.DataFrame(data={'date':date_index})] + check_lst, axis=1)
        
        return df_all

class table_generator:
    def __init__(self, start, end, staff_name):
        self.calendar=hiCalendar(start, end)
        self.staff_name=staff_name
        self.staff=db_session.query(Staffs).filter(Staffs.staff_name==staff_name).scalar()

    def gen_table(self, table_cls):
        df = pd.read_sql(
            sql = db_session.query(table_cls).filter(table_cls.staff_name==self.staff_name).statement,
            con = engine
        )
        return df

    def check_dataframe(self):
        date_index = self.calendar.date_index.date
        out_dict = {}
        for i in self.staff.checkout_time:
            out_dict[i.created_time.date()]=i.created_time
        out_lst = [out_dict[i].time() if i in out_dict.keys() else None for i in date_index]

        in_dict = {}
        for i in self.staff.checkin_time:
            in_dict[i.created_time.date()]=i.created_time
        in_lst = [in_dict[i].time() if i in in_dict.keys() else None for i in date_index]
        
        worktime_dict = {}
        for i in date_index:
            if (in_dict.get(i) != None) and (out_dict.get(i) != None):
                worktime_dict[i] = (out_dict[i].timestamp() - in_dict[i].timestamp())/60/60
        worktime_lst = [round(worktime_dict[i],2) if i in worktime_dict.keys() else 0 for i in date_index]
        agg_lst = [round(sum(worktime_lst[:i+1]),2) for i in range(len(worktime_lst))]

        df = pd.DataFrame(data={'date':self.calendar.date_index, 'checkin':in_lst, 'checkout':out_lst, 'worktime[hr]':worktime_lst, 'aggregation[hr]':agg_lst})
        df['date'] = df['date'].dt.strftime("%m/%d/%Y, %A")
        df.iloc[:] = df.iloc[::-1].values

        required_hours = (self.calendar.bdays_bool_df() * 9).sum()[0]
        
        return df, required_hours

##======================line_msg==================================
def moment_bubble(check: str, img_url: str, staff_name: str, now: str, moment='Pls Select Date/Time'):
    '''
    check: 'checkin' or 'checkout' or 'take a leave'
    '''
    if check == 'checkin':
        datetimepicker = DatetimePickerAction(
                            label="moment",
                            data=f'id=0&staff_name={staff_name}&check={check}',
                            mode='datetime',
                            initial=now.strftime("%Y-%m-%dT%H:%M"),
                            max = now.strftime("%Y-%m-%dT")+'23:59',
                            min = now.strftime("%Y-%m-%dT%H:%M")
                            )
    elif check == 'checkout':
        datetimepicker = DatetimePickerAction(
                            label="moment",
                            data=f'id=0&staff_name={staff_name}&check={check}',
                            mode='datetime',
                            initial=now.strftime("%Y-%m-%dT%H:%M"),
                            min = now.strftime("%Y-%m-%dT")+'00:00',
                            max = now.strftime("%Y-%m-%dT%H:%M")
                            )
    elif '_Leave' in check :
        datetimepicker = DatetimePickerAction(
                            label="moment",
                            data=f'id=0&staff_name={staff_name}&check={check}',
                            mode='datetime',
                            initial=now.strftime("%Y-%m-%dT%H:%M"),
                            min = now.strftime("%Y-%m-%dT%H:%M")
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
                            text=f"{check} @ {moment}",
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

def check_bubble(check: str, staff_name: str, moment='Pls Select Date/Time'):
    bubble = BubbleContainer(
                direction='ltr',
                body=BoxComponent(
                    layout='vertical',
                    spacing='sm',
                    contents=[
                        TextComponent(
                            text=f"{check} {staff_name} @ {moment}",
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
                                label="Revise",
                                data=f'id=1&staff_name={staff_name}&check={check}',
                            )
                        ),
                        ButtonComponent(
                            style='primary',
                            action=PostbackAction(
                                label="That's it",
                                data=f'id=2&staff_name={staff_name}&check={check}&moment={moment}',
                            )
                        )
                    ]
                )
            )
    return FlexSendMessage(alt_text=f'Hi {staff_name}, {check} yourself!', contents=bubble)

def reply_dash_msg():
    pass

if __name__ == "__main__":
    season_table_generator(year=2022, season='Q1').check_dataframe()