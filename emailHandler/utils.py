from flask_mail import Mail, Message
import os

from utils.definitions import *
from flask import render_template

mail = Mail()

def loadEmailConfigs():
    try:
        os.environ['MAIL_USERNAME'] = (open('mail_username', 'r').readline()).strip()
        os.remove('mail_username')
        os.environ['MAIL_PASSWORD'] = (open('mail_password', 'r').readline()).strip()
        os.remove('mail_password')
    except Exception:
        pass

def sendVerificationEmail(recipient, token):
    msg = Message(subject = 'Yell Account Verification', sender = os.environ.get('MAIL_USERNAME'), recipients = [recipient])
    msg.html = render_template('email_template.html', link = 'https://google.com/api/account/verify/' + token)
    mail.send(msg)