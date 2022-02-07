from flask import current_app as app
from flask import render_template, request, abort
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *



# custom
import config
import db

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
            msg_reply = TextSendMessage(text=f'Hi {staff_integrity.staff_name}, welcome to ur office. Pls Process in the web')

    if (msg_reply is None): 
        msg_reply = [
            TextSendMessage(text='''Not your business''')
        ]
    
    config.line_bot_api.reply_message(
        event.reply_token,
        msg_reply
        )

if __name__ == "__main__":
    pass