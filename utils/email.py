from flask_mail import Mail, Message
import os

from utils.definitions import *
from flask import render_template

mail = Mail()

def sendVerificationEmail(recipient, token, recipient_name):
    msg = Message(subject = 'Yell Account Verification', sender = ('Yell', os.environ.get('MAIL_USERNAME')), recipients = [recipient])
    msg.html = render_template('email_template.html', link = os.environ.get('YELL_MAIN_URL', '') + '/api/account/verify/' + token, name = recipient_name)
    mail.send(msg)