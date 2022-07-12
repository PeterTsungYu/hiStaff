from cgi import test
from flask import current_app as app
from flask import render_template, request, abort, redirect, url_for
import requests 
import json
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
from urllib.parse import quote, parse_qsl, parse_qs
from pytz import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
def strptime(time) -> datetime:   
    if 't' in time:
        return datetime.strptime(time[2:], '%y-%m-%dt%H:%M')
    else:
        return datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
def strf_datetime(dt) -> str:
    date_args = [u for i in dt.split(',') for u in i.split(' ') if all([u != cond for cond in ['','PM','AM']])]
    #config.logger.debug(date_args)
    time_args = date_args[-1].split(':')
    #config.logger.debug(time_args)
    return str(datetime(
                year=int(date_args[2]), month=int(datetime.strptime(date_args[0], "%b").month), day=int(date_args[1]), 
                hour=int(time_args[0]), minute=int(time_args[1]), second=int(time_args[2]))
                )

import haversine as hs

# custom
import config
import db

checkin_img_url = "https://img.onl/f41SeX"
checkout_img_url = "https://img.onl/BMdSLf"

##======================schedulers==================================
twtz = timezone('Asia/Taipei')
sched = BackgroundScheduler(timezone=twtz)
sched.start()

# update deferred leave every staff every first day of month 
@sched.scheduled_job('cron', id='sched_update_deferred_leave', day=1)
def sched_update_deferred_leave():
    if  datetime.now().month == 1:
        year = datetime.now().year - 1
        last_month = 12
    else:
        year = datetime.now().year
        last_month = datetime.now().month - 1
    sched_msg = db.all_table_generator(year=year, month=last_month).update_deferred_leave()
    print(sched_msg)
    print(db.db_session)

##======================routes==================================
@app.before_request
def init_tables():
    db.init_db()
    config.logger.debug('Staff table is up to date')

# an “on request end” event
# automatically remove database sessions at the end of the request 
# or when the application shuts down
@app.teardown_appcontext
def shutdown_session(exception=None):
    db.db_session.remove()


@app.route('/')
def home():
    """Landing page."""
    return render_template(
        'index.jinja2',
        title='Plotly Dash Flask Tutorial',
        description='Embed Plotly Dash into your Flask applications.',
        template='home-template',
        body="This is a homepage served with Flask."
    ) 

'''
@app.route('/staff')
def staff():
    d = dict(parse_qsl(request.args.get('liff.state')))
    print(request.url)
    if d.get('/date_check/name') != None:
        redirect_url = f'{url_for(f".{config.dash_prefix}/", _external=False)}date_check?staff={d.get("/date_check/name")}' #http://localhost:5003/hiStaff_dashapp/...
    elif d.get('/season_check/name') != None:
        redirect_url = f'{url_for(f".{config.dash_prefix}/", _external=False)}season_check?staff={d.get("/season_check/name")}' #http://localhost:5003/hiStaff_dashapp/...
    elif d.get('/leave_form/name') != None:
        redirect_url = f'{url_for(f".{config.dash_prefix}/", _external=False)}leave_form?staff={d.get("/leave_form/name")}' #http://localhost:5003/hiStaff_dashapp/...
        print(redirect_url)
    return redirect(redirect_url)
'''

@config.handler.add(FollowEvent)
def handle_follow(event):
    db.get_or_create_user(event.source.user_id)

    config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='welcome to linebot!'))


@config.handler.add(UnfollowEvent)
def handle_unfollow(event):
    config.logger.debug(event)
    unfollowing_user = db.get_or_create_user(event.source.user_id)
    print(f'Unfollow event from {unfollowing_user}')


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    #app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        config.handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@config.handler.add(MessageEvent, message=LocationMessage)
def handle_message(event):
    print(event)
    address = event.message.address
    latitude = event.message.latitude
    longitude = event.message.longitude
    title = event.message.title
    current_loc = (event.message.latitude, event.message.longitude)
    office_loc = (24.8457148, 121.0182065)
    print(address, latitude, longitude, title)

    user_id = event.source.user_id
    user = db.get_or_create_user(user_id=user_id)
    staff_integrity = db.db_session.query(db.Staffs).filter(db.Staffs.staff_name == user.nick_name).scalar()
    if staff_integrity != None:
        if title != "hiPower GreenTech":
            distance = hs.haversine(current_loc,office_loc)
            if distance <= 0.5:
                location = 'office'
            elif title:
                location = title
            else:
                location = 'remote'
            msg_reply = TextSendMessage(
                text=f"Select Check Type if correct location",
                quick_reply=QuickReply(
                    items=[
                        QuickReplyButton(action=PostbackAction(
                            label="Check In",
                            data=f'id=0&staff_name={staff_integrity.staff_name}&check=checkin&location={location}',
                            )),
                        QuickReplyButton(action=PostbackAction(
                            label="Check Out",
                            data=f'id=0&staff_name={staff_integrity.staff_name}&check=checkout&location={location}',
                            )),
                        QuickReplyButton(action=LocationAction(f"Send location")),
                    ]
                    )
                )
            config.line_bot_api.reply_message(
                event.reply_token,
                msg_reply
                )


@config.handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print(event)
    now_datetime = datetime.now()

    msg_source = event.source.type
    msg_text = str(event.message.text).lower()
    msg_reply = None

    if msg_source == 'group':
        group_id = event.source.group_id
    else:
        user_id = event.source.user_id
        user = db.get_or_create_user(user_id=user_id)
        staff_integrity = db.db_session.query(db.Staffs).filter(db.Staffs.staff_name == user.nick_name).scalar()
        if staff_integrity != None:
            if msg_text in ['check in', 'check out']:
                msg_reply = TextSendMessage(
                    text=f"Share your location",
                    quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(action=LocationAction(f"Send location")),
                        ]
                        )
                    )
                #msg_reply = db.moment_bubble(check='checkin', img_url=checkin_img_url, staff_name=staff_integrity.staff_name, now = now_datetime)
                #msg_reply = db.moment_bubble(check='checkout', img_url=checkout_img_url, staff_name=staff_integrity.staff_name, now = now_datetime)
            elif msg_text in ['personal dashboard']:
                msg_reply = [TemplateSendMessage(alt_text='Your dashboard',
                                                template=ButtonsTemplate(text='Peek ur dashboard',
                                                                        actions=[URIAction(label=f"Check Table", 
                                                                                        uri=f'https://rvproxy.fun2go.co/hiStaff_dashapp/date_check?staff={staff_integrity.staff_name}'),
                                                                                URIAction(label=f"Season Table", 
                                                                                        uri=f'https://rvproxy.fun2go.co/hiStaff_dashapp/season_check?staff={staff_integrity.staff_name}')
                                                                                        ]
                                                                    )
                                                                    ),
                            #TextSendMessage(text=f'Your personal check table: {config.dash_liff}/date_check/name={staff_integrity.staff_name}'),
                            #TextSendMessage(text=f'Your personal Season table: {config.dash_liff}/season_check/name={staff_integrity.staff_name}')
                            ]
            elif msg_text in ['take a leave_start']:
                msg_reply = TemplateSendMessage(alt_text='Take a Leave',
                                                template=ButtonsTemplate(text='Take a Leave',
                                                                        actions=[URIAction(label=f"Leave Form", 
                                                                                        uri=f'https://rvproxy.fun2go.co/hiStaff_dashapp/leave_form?staff={staff_integrity.staff_name}'),
                                                                        ])
                                                ),
                

    if (msg_reply != None) and (msg_source != 'group'): 
        config.line_bot_api.reply_message(
            event.reply_token,
            msg_reply
            )


@config.handler.add(PostbackEvent)
def handle_postback(event):

    now_datetime = datetime.now()

    data = event.postback.data
    back_dict = dict(parse_qsl(data))
    params = event.postback.params
    config.logger.debug(back_dict)

    # check in or out moment handler
    if any([s in data for s in ('checkin', 'checkout')]) or ('_Leave' in data):
        id = back_dict.get('id')
        staff_name = back_dict.get('staff_name')
        check = back_dict.get('check')
        moment = back_dict.get('moment')
        location = back_dict.get('location')
        
        share_loc_msg = TextSendMessage(
            text=f"Share your {check} location",
            quick_reply=QuickReply(
                items=[
                   QuickReplyButton(action=LocationAction(f"Send {check} location")),
                ]
                )
            )

        try:
            if (id == '0'):
                msg_reply = db.location_bubble(check=check, staff_name=staff_name, location=location)
            elif (id == '1'):
                msg_reply = TextSendMessage(
                    text=f"Share your location",
                    quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(action=LocationAction(f"Send location")),
                        ]
                        )
                    )
            elif id == '2': 
                if check == 'checkin':
                    img_url = checkin_img_url
                elif check == 'checkout':
                    img_url = checkout_img_url
                msg_reply = db.moment_bubble(check=check, img_url=img_url ,staff_name=staff_name, now=now_datetime, location=location)
            elif (id == '3') and (params != None): # id=0 action=datetimepicker 
                _datetime = strptime(event.postback.params.get('datetime').lower())
                msg_reply = db.check_bubble(check=check, staff_name=staff_name, moment=_datetime, location=location)
            elif id == '4': 
                moment = strptime(moment)
                # check in and check out table should be compared
                config.logging.debug(datetime.now())
                last_checkin = db.db_session.query(db.CheckIn).filter(db.CheckIn.staff_name == staff_name).order_by(db.CheckIn.id.desc()).first()
                last_checkout = db.db_session.query(db.CheckOut).filter(db.CheckOut.staff_name == staff_name).order_by(db.CheckOut.id.desc()).first()
                now = datetime.now()
                config.logging.debug(now)
                if check == 'checkin':
                    for i in [0,1]:    
                        if i == 0: 
                        # compared to the last check
                            if (last_checkin != None):
                                last_checkin_moment = last_checkin.created_time
                                # case: check already
                                if (moment.year == last_checkin_moment.year) and (moment.month == last_checkin_moment.month) and (moment.day == last_checkin_moment.day):
                                    msg_reply = TextSendMessage(text=f'Do not check twice. It is not an exam.')
                                    break
                        elif i == 1:
                        # case: check correctly or first time check
                            checkin = db.CheckIn(staff_name=staff_name, created_time=moment, check_place=location)
                            db.db_session.add(checkin)
                            db.db_session.commit()
                            if (moment.hour > 8) :
                                msg_reply = [TextSendMessage(text=f'Succeed to {check}\nYou are late! Slacker!')]
                            elif (moment.hour == 8) and (moment.hour > 30):
                                msg_reply = [TextSendMessage(text=f'Succeed to {check}\nClose...but you are still late!')]
                            else:
                                msg_reply = [TextSendMessage(text=f'Succeed to {check}\nWish you have a good day. Mate!')]  
                        '''
                        # case: check prior
                        if i == 1 and (now.timestamp() - moment.timestamp()) > (30*60): 
                            msg_reply = TextSendMessage(text=f'Do not check prior. Be honest 0.0')
                        '''    
                elif check == 'checkout': 
                    for i in [0,1,2]:
                        if i == 0:
                        # compared to the last check
                            if last_checkout != None:
                                last_checkout_moment = last_checkout.created_time
                                # case: check already
                                if (moment.year == last_checkout_moment.year) and (moment.month == last_checkout_moment.month) and (moment.day == last_checkout_moment.day):
                                    msg_reply = TextSendMessage(text=f'Do not check twice. It is not an exam.')
                                    break
                        # case: compared to the checkin table
                        elif i == 1:
                            if  last_checkin != None:
                                last_checkin_moment = last_checkin.created_time
                                if (moment.year == last_checkin_moment.year) and (moment.month == last_checkin_moment.month) and (moment.day != last_checkin_moment.day):
                                    msg_reply = TextSendMessage(text=f'Forgot to check yourself in, silly u.')
                                    continue
                                elif moment.timestamp() < last_checkin_moment.timestamp():
                                    msg_reply = TextSendMessage(text=f'Checkin @ {last_checkin_moment}. How on earth can u reverse the time?')
                                    break
                            else:
                                msg_reply = TextSendMessage(text=f"U've never checked in before. Unbelievable.")
                                continue
                            # case: check correctly and first time check
                        elif i == 2:
                            checkout = db.CheckOut(staff_name=staff_name, created_time=moment, check_place=location)
                            print('check here')
                            db.db_session.add(checkout)
                            db.db_session.commit()
                            if (moment.hour > 17) :
                                msg_reply = [TextSendMessage(text=f'Succeed to {check}\nGood day, Worker!')]
                            elif (moment.hour == 17) and (moment.hour < 30):
                                msg_reply = [TextSendMessage(text=f'Succeed to {check}\nEfficiency is your motto!')]
                            else:
                                msg_reply = [TextSendMessage(text=f'Succeed to {check}\nWish you have a good day. Mate!')] 
                        '''
                        # case: check belatedly
                        if i == 2 and (moment.timestamp() - now.timestamp()) > (60*3):
                            msg_reply = TextSendMessage(text=f'Do not check belatedly. Be honest 0.0')
                        '''    
                elif '_Leave_start' in check :
                    try:
                        db.db_session.add(db.Leaves(staff_name=staff_name, start=moment, type=db.leaves_type[check.strip('_start')]['type']))
                        db.db_session.commit()
                        msg_reply = [
                            TextSendMessage(text=f'Succeed to take {check}'),
                            db.moment_bubble(check=check.strip('_start')+'_end', img_url=checkout_img_url, staff_name=staff_name, now = now_datetime),
                        ]
                    except:
                        msg_reply = TextSendMessage(text=f'Unsucceessful {check}')

                elif '_Leave_end' in check:
                    try:
                        check = check.strip("end").strip("_")
                        _entry = db.db_session.query(db.Leaves).filter(db.Leaves.staff_name==staff_name, db.Leaves.type==db.leaves_type[check.strip('_start')]['type']).order_by(db.Leaves.id.desc()).first()
                        if moment >= _entry.start:
                            db.db_session.query(db.Leaves).\
                            filter(db.Leaves.staff_name==staff_name, db.Leaves.id==_entry.id).\
                            update({"end": moment})
                            db.db_session.commit()
                            msg_reply = TextSendMessage(text=f'Succeed to take {check}')
                            config.line_bot_api.push_message("C9773535cc835cf00cc3df02db9f57b1b", TextSendMessage(text=f'{staff_name} takes {check} from {_entry.start} to {moment}'))
                        else:
                            msg_reply = [
                                TextSendMessage(text=f'Unsucceessful {check}. Leave Start > Leave_End.'),
                                db.moment_bubble(check=check+'_end', img_url=checkout_img_url, staff_name=staff_name, now=now_datetime),
                            ]
                    except:
                        msg_reply = TextSendMessage(text=f'Unsucceessful {check}')

            config.line_bot_api.reply_message(event.reply_token, msg_reply)

        except AttributeError as e:
            print(e)

if __name__ == "__main__":
    pass