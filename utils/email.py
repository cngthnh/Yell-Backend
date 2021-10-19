from flask_mail import Mail, Message
import os

import threading
from utils.definitions import *
from flask import render_template, copy_current_request_context

mail = Mail()

def sendEmailAsync(msg):
    @copy_current_request_context
    def sendMessage(msg):
        mail.send(msg)

    sender = threading.Thread(name='mail_sender', target=sendMessage, args=(msg,))
    sender.start()

def sendVerificationEmail(recipient, token, recipient_name):
    msg = Message(subject = 'Yell Account Verification', sender = ('Yell', os.environ.get('MAIL_USERNAME')), recipients = [recipient])
    msg.html = render_template('email_template.html', link = os.environ.get('YELL_MAIN_URL', '') + '/api/account/verify/' + token, name = recipient_name)
    msg.body = render_template('')
    sendEmailAsync(msg)