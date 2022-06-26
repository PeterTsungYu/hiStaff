from wtforms import Form, BooleanField, StringField, PasswordField, validators

class LeaveForm(Form):
    staff_name = StringField('Staff Name', [validators.Length(min=1, max=)])
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    accept_tos = BooleanField('I accept the TOS', [validators.DataRequired()])
