from cgi import test
from flask import current_app as app
from flask import render_template, request, abort, redirect, url_for
import requests 
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
from urllib.parse import quote, parse_qsl, parse_qs
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


# custom
import config
import db

checkin_img_url = "https://img.onl/f41SeX"
checkout_img_url = "https://img.onl/BMdSLf"
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

@app.route('/staff')
def staff():
    d = dict(parse_qsl(request.args.get('liff.state')))
    if d.get('/checkin/name') != None:
        redirect_url = f'{url_for(f".{config.dash_prefix}/", _external=False)}checkin?staff={d.get("/checkin/name")}' #https://rvproxy.fun2go.energy/hiStaff_dashapp
    elif d.get('/checkout/name') != None:
        redirect_url = f'{url_for(f".{config.dash_prefix}/", _external=False)}checkout?staff={d.get("/checkout/name")}' #https://rvproxy.fun2go.energy/hiStaff_dashapp
    return redirect(redirect_url)


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
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        config.handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@config.handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    user_id = event.source.user_id
    user = db.get_or_create_user(user_id=user_id)
    msg_text = str(event.message.text).lower()
    msg_reply = None

    staff_integrity = db.db_session.query(db.Staffs).filter(db.Staffs.staff_name == user.nick_name).scalar()
    if staff_integrity != None:
        if msg_text in ['check in']:
            msg_reply = db.moment_bubble(check='checkin', img_url=checkin_img_url, staff_name=staff_integrity.staff_name)
        elif msg_text in ['check out']:
            msg_reply = db.moment_bubble(check='checkout', img_url=checkout_img_url, staff_name=staff_integrity.staff_name)
        elif msg_text in ['personal dashboard']:
            msg_reply = TemplateSendMessage(alt_text='Your dashboard',
                                            template=ButtonsTemplate(text='Peek ur dashboard',
                                                                    actions=[URIAction(label=f"{staff_integrity.staff_name}'s CheckIn Dash", 
                                                                                    uri=f'{config.dash_liff}/checkin/name={staff_integrity.staff_name}'),
                                                                            URIAction(label=f"{staff_integrity.staff_name}'s CheckOut Dash", 
                                                                                    uri=f'{config.dash_liff}/checkout/name={staff_integrity.staff_name}')
                                                                                    ]
                                                                )
                                                                )


    if (msg_reply is None): 
        msg_reply = [
            TextSendMessage(text='''Not your business''')
        ]
    
    config.line_bot_api.reply_message(
        event.reply_token,
        msg_reply
        )

@config.handler.add(PostbackEvent)
def handle_postback(event):
    data = event.postback.data
    back_dict = dict(parse_qsl(data))
    params = event.postback.params
    config.logger.debug(back_dict)

    # check in or out moment handler
    if any([s in data for s in ('checkin', 'checkout')]):
        id = back_dict.get('id')
        staff_name = back_dict.get('staff_name')
        check = back_dict.get('check')
        moment = back_dict.get('moment') # postback from id=2
        
        try:
            if (id == '0') and (params != None): # id=0 action=datetimepicker
                _moment = strptime(event.postback.params.get('datetime').lower())
                msg_reply = db.check_bubble(check=check, staff_name=staff_name, moment=_moment)
                #msg_reply = TextSendMessage(text=f'{data} @ {moment}')
            elif id == '1': # id=1 action=postback
                if check == 'checkin':
                    img_url = checkin_img_url
                else:
                    img_url = checkout_img_url
                msg_reply = db.moment_bubble(check=check, img_url=img_url ,staff_name=staff_name)
            elif id == '2': # id=2 action=postback
                moment = strptime(moment)
                # check in and check out table should be compared
                config.logging.debug(datetime.now())
                last_checkin = db.db_session.query(db.CheckIn).filter(db.CheckIn.staff_name == staff_name).order_by(db.CheckIn.id.desc()).first()
                last_checkout = db.db_session.query(db.CheckOut).filter(db.CheckOut.staff_name == staff_name).order_by(db.CheckOut.id.desc()).first()
                now = datetime.now()
                config.logging.debug(now)
                if check == 'checkin':
                    for i in [0,1]:    
                        if i == 0 and last_checkin != None:
                            last_checkin_moment = last_checkin.created_time
                            # case: check already
                            if (moment.year == last_checkin_moment.year) and (moment.month == last_checkin_moment.month) and (moment.day == last_checkin_moment.day):
                                msg_reply = TextSendMessage(text=f'Do not check twice. It is not an exam.')
                                break
                            # case: first time check
                            else:
                                continue
                        # case: check prior
                        if i == 1 and (now.timestamp() - moment.timestamp()) >= 120: 
                            msg_reply = TextSendMessage(text=f'Do not check prior. Be honest 0.0')
                        # case: check correctly
                        else: 
                            checkin = db.CheckIn(staff_name=staff_name, created_time=moment)
                            db.db_session.add(checkin)
                            db.db_session.commit()
                            if (moment.hour > 8) :
                                msg_reply = [TextSendMessage(text=f'Succeed to {check}'), TextSendMessage(text='You are late! Slacker!')]
                            elif (moment.hour == 8) and (moment.hour > 30):
                                msg_reply = [TextSendMessage(text=f'Succeed to {check}'), TextSendMessage(text='Close...but you are still late!')]
                            else:
                                msg_reply = [TextSendMessage(text=f'Succeed to {check}'), TextSendMessage(text='Wish you have a good day. Mate!')]  
                else: # elif check == 'checkout': 
                    for i in [0,1,2]:
                        if i == 0 and last_checkout != None:
                            last_checkout_moment = last_checkout.created_time
                            # case: check already
                            if (moment.year == last_checkout_moment.year) and (moment.month == last_checkout_moment.month) and (moment.day == last_checkout_moment.day):
                                msg_reply = TextSendMessage(text=f'Do not check twice. It is not an exam.')
                                break
                            # case: first time check
                            else:
                                continue
                        # case: compared to the other check table
                        if i == 1 and last_checkin != None:
                            last_checkin_moment = last_checkin.created_time
                            if (moment.year == last_checkin_moment.year) and (moment.month == last_checkin_moment.month) and (moment.day != last_checkin_moment.day):
                                msg_reply = TextSendMessage(text=f'Forgot to check yourself in, silly u.')
                                break
                            elif moment.timestamp() < last_checkin_moment.timestamp():
                                msg_reply = TextSendMessage(text=f'Checkin @ {last_checkin_moment}. How on earth can u reverse the time?')
                                break
                            else:
                                continue
                        # case: check belatedly
                        if i == 2 and (moment.timestamp() - now.timestamp()) >= 120:
                            msg_reply = TextSendMessage(text=f'Do not check belatedly. Be honest 0.0')
                        # case: check correctly
                        else:
                            checkout = db.CheckOut(staff_name=staff_name, created_time=moment)
                            db.db_session.add(checkout)
                            db.db_session.commit()
                            if (moment.hour > 17) :
                                msg_reply = [TextSendMessage(text=f'Succeed to {check}'), TextSendMessage(text='Good day, Worker!')]
                            elif (moment.hour == 17) and (moment.hour < 30):
                                msg_reply = [TextSendMessage(text=f'Succeed to {check}'), TextSendMessage(text='Efficiency is your motto!')]
                            else:
                                msg_reply = [TextSendMessage(text=f'Succeed to {check}'), TextSendMessage(text='Wish you have a good day. Mate!')] 
            config.line_bot_api.reply_message(event.reply_token, msg_reply)

        except AttributeError as e:
            print(e)


if __name__ == "__main__":
    pass