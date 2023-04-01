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
        return datetime.strptime(time, '%Y-%m-%d %H:%M')
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

check_img_url = "https://img.onl/0P7lSa"

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
'''
@app.before_request
def init_tables():
    db.init_db()
    config.logger.debug('Staff table is up to date')
'''

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
            TextSendMessage(text='歡迎加入!請向管理員索取使用[打卡服務]的權限'))


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
    staff_integrity = db.db_session.query(db.Staffs).filter(db.Staffs.uuid == user.id).scalar()
    if staff_integrity != None:
        distance = hs.haversine(current_loc,office_loc)
        if distance <= 1:
            location = 'office'
        elif title:
            location = title
        else:
            location = address
        msg_reply = TextSendMessage(
            text=f"如果你的分享地點是正確的話，請接著選擇打卡的形式",
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(action=PostbackAction(
                        label="上班打卡 Check In",
                        data=f'id=0&staff_name={staff_integrity.staff_name}&check=checkin&location={location}',
                        )),
                    QuickReplyButton(action=PostbackAction(
                        label="下班打卡 Check Out",
                        data=f'id=0&staff_name={staff_integrity.staff_name}&check=checkout&location={location}',
                        )),
                    QuickReplyButton(action=LocationAction(f"分享位置")),
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
        staff_integrity = db.db_session.query(db.Staffs).filter(db.Staffs.uuid == user.id).scalar()
        if staff_integrity != None:
            if msg_text in ['check in', 'check out']:
                msg_reply = TextSendMessage(
                    text=f"分享位置",
                    quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(action=LocationAction(f"分享位置")),
                        ]
                        )
                    )
                #msg_reply = db.moment_bubble(check='checkin', img_url=checkin_img_url, staff_name=staff_integrity.staff_name, now = now_datetime)
                #msg_reply = db.moment_bubble(check='checkout', img_url=checkout_img_url, staff_name=staff_integrity.staff_name, now = now_datetime)
            elif msg_text in ['personal dashboard']:
                msg_reply = [TemplateSendMessage(alt_text='專屬紀錄表',
                                                template=ButtonsTemplate(text='選擇一個紀錄表',
                                                                        actions=[URIAction(label=f"打卡紀錄表", 
                                                                                        uri=f'https://rvproxy.fun2go.co/hiStaff_dashapp/date_check?staff={staff_integrity.uuid}'),
                                                                                URIAction(label=f"季紀錄表", 
                                                                                        uri=f'https://rvproxy.fun2go.co/hiStaff_dashapp/season_check?staff={staff_integrity.uuid}')
                                                                                        ]
                                                                    )
                                                                    ),
                            #TextSendMessage(text=f'Your personal check table: {config.dash_liff}/date_check/name={staff_integrity.staff_name}'),
                            #TextSendMessage(text=f'Your personal Season table: {config.dash_liff}/season_check/name={staff_integrity.staff_name}')
                            ]
            elif msg_text in ['take a leave_start']:
                msg_reply = TemplateSendMessage(alt_text='請假',
                                                template=ButtonsTemplate(text='請假',
                                                                        actions=[URIAction(label=f"請假表", 
                                                                                        uri=f'https://rvproxy.fun2go.co/hiStaff_dashapp/leave_form?staff={staff_integrity.uuid}'),
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

        try:
            if id == '0':
                msg_reply = db.check_bubble(check=check, staff_name=staff_name, moment=now_datetime.strftime("%Y-%m-%d %H:%M"), location=location)
            elif id == '1':
                msg_reply = TextSendMessage(
                    text=f"分享位置",
                    quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(action=LocationAction(f"分享位置")),
                        ]
                        )
                    )
            elif id == '2': 
                moment = strptime(moment)
                print(moment)
                print(now_datetime)
                if (now_datetime.timestamp() - moment.timestamp()) <= (5*60): 
                    # check in and check out table should be compared
                    last_checkin = db.db_session.query(db.CheckIn).filter(db.CheckIn.staff_name == staff_name).order_by(db.CheckIn.id.desc()).first()
                    last_checkout = db.db_session.query(db.CheckOut).filter(db.CheckOut.staff_name == staff_name).order_by(db.CheckOut.id.desc()).first()
                    if check == 'checkin':
                        for i in [0,1]:    
                            if i == 0: 
                            # compared to the last check
                                if (last_checkin != None):
                                    last_checkin_moment = last_checkin.created_time
                                    # case: check already
                                    if (moment.year == last_checkin_moment.year) and (moment.month == last_checkin_moment.month) and (moment.day == last_checkin_moment.day):
                                        msg_reply = TextSendMessage(text=f'請不要重複打卡喔')
                                        break
                            elif i == 1:
                            # case: check correctly or first time check
                                checkin = db.CheckIn(staff_name=staff_name, created_time=moment, check_place=location)
                                db.db_session.add(checkin)
                                db.db_session.commit()
                                # if (moment.hour > 8) :
                                #     msg_reply = [TextSendMessage(text=f'成功! {check}\n但好像遲到了')]
                                # elif (moment.hour == 8) and (moment.hour > 30):
                                #     msg_reply = [TextSendMessage(text=f'成功! {check}\nClose...but you are still late!')]
                                # else:
                                #     msg_reply = [TextSendMessage(text=f'Succeed to {check}\nWish you have a good day. Mate!')]  
                                msg_reply = [TextSendMessage(text=f'送出成功! {check}\n祝你有個美好的一天!')]
                    elif check == 'checkout': 
                        for i in [0,1,2]:
                            if i == 0:
                            # compared to the last check
                                if last_checkout != None:
                                    last_checkout_moment = last_checkout.created_time
                                    # case: check already
                                    if (moment.year == last_checkout_moment.year) and (moment.month == last_checkout_moment.month) and (moment.day == last_checkout_moment.day):
                                        msg_reply = TextSendMessage(text=f'請不要重複打卡喔')
                                        break
                            # case: compared to the checkin table
                            elif i == 1:
                                if  last_checkin != None:
                                    last_checkin_moment = last_checkin.created_time
                                    if (moment.year == last_checkin_moment.year) and (moment.month == last_checkin_moment.month) and (moment.day != last_checkin_moment.day):
                                        msg_reply = TextSendMessage(text=f'你是不是忘記上班打卡了?')
                                        continue
                                    elif moment.timestamp() < last_checkin_moment.timestamp():
                                        msg_reply = TextSendMessage(text=f'Checkin @ {last_checkin_moment}. 你的上下班時間怎麼顛倒了?')
                                        break
                                else:
                                    msg_reply = TextSendMessage(text=f"你從來沒有上班打卡過耶...")
                                    continue
                                # case: check correctly and first time check
                            elif i == 2:
                                checkout = db.CheckOut(staff_name=staff_name, created_time=moment, check_place=location)
                                db.db_session.add(checkout)
                                db.db_session.commit()
                                if (moment.hour > 17) :
                                    msg_reply = [TextSendMessage(text=f'成功! {check}\n下班囉!')]
                                elif (moment.hour == 17) and (moment.hour < 30):
                                    msg_reply = [TextSendMessage(text=f'成功! {check}\n很有效率結束一天的工作!')]
                                else:
                                    msg_reply = [TextSendMessage(text=f'成功! {check}\n祝你有個美好的句點!')] 
                else:
                    msg_reply = [TextSendMessage(text=f'超時5分鐘的打卡，請重新打卡')] 

            config.line_bot_api.reply_message(event.reply_token, msg_reply)

        except AttributeError as e:
            print(e)

if __name__ == "__main__":
    #config.line_bot_api.push_message("C9773535cc835cf00cc3df02db9f57b1b", TextSendMessage(text=f'{staff_name} takes {check} from {_entry.start} to {moment}'))
    pass
