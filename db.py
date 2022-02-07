from flask import current_app as app
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, inspect, UniqueConstraint
from datetime import datetime
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

import config

engine = create_engine(config.db_path, convert_unicode=True)
#print(engine)

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=True, bind=engine))
# When True, all query operations will issue a Session.flush() call to this Session before proceeding
# It’s typical that autoflush is used in conjunction with autocommit=False
# The Session object features autobegin the tx state, so that normally it is not necessary to call the Session.begin() method explicitly.

Base = declarative_base()
Base.query = db_session.query_property()

##======================DB==================================
@app.before_first_request
def init_tables():
    result = init_db()
    if result:
        db_session.add_all(staff_lst) # a way to insert many query
        db_session.commit()
        config.logger.debug('create staffs')

# an “on request end” event
# automatically remove database sessions at the end of the request 
# or when the application shuts down
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

def init_db():
    if inspect(engine).has_table('staffs'):
        return False
    else:    
        Base.metadata.create_all(bind=engine)
        return True


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
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    nick_name = Column(String)
    image_url = Column(String(length=256))
    created_time = Column(DateTime, default=datetime.now())
    def __repr__(self):
        return f'<User {self.nick_name!r}>'

class Staffs(Base):
    __tablename__ = 'staffs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_name = Column(String)
    def __repr__(self):
        return f'<User {self.staff_name!r}>'

staff_lst = [Staffs(staff_name='謝宗佑'),]



if __name__ == "__main__":
    pass
