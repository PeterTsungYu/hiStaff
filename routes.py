from flask import current_app as app
from flask import render_template, request, abort
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
from urllib.parse import quote, parse_qsl
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
@app.before_first_request
def init_tables():
    result = db.init_db()
    if result:
        db.db_session.add_all(db.staff_lst) # a way to insert many query
        db.db_session.commit()
        config.logger.debug('create staffs_table')

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
        now = datetime.now()
        
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
                print(now)
                print(moment)
                if check == 'checkin':
                    last_entry = db.db_session.query(db.CheckIn).filter(db.CheckIn.staff_name == staff_name).order_by(db.CheckIn.id.desc()).first()
                    last_moment = last_entry.created_time
                    if (now.timestamp() - moment.timestamp()) >= 120:
                        msg_reply = TextSendMessage(text=f'Do not check prior. Be honest 0.0')
                    elif (now.year == last_moment.year) and (now.month == last_moment.month) and (now.day == last_moment.day):
                        msg_reply = TextSendMessage(text=f'Do not check twice. It is not an exam.')
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
                else:
                    last_entry = db.db_session.query(db.CheckOut).filter(db.CheckOut.staff_name == staff_name).order_by(db.CheckOut.id.desc()).first()
                    if (moment.timestamp() - now.timestamp()) >= 120:
                        msg_reply = TextSendMessage(text=f'Do not check belatedly. Be honest 0.0')
                    elif last_entry != None:
                        last_moment = last_entry.created_time
                        if (now.year == last_moment.year) and (now.month == last_moment.month) and (now.day == last_moment.day):
                            msg_reply = TextSendMessage(text=f'Do not check twice. It is not an exam.')
                        else:
                            pass
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