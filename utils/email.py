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
    link = os.environ.get('YELL_MAIN_URL', '') + EMAIL_VRF_ENDPOINT + token
    msg.html = render_template(EMAIL_VRF_TEMPLATE_HTML, link = link, name = recipient_name)
    msg.body = render_template(EMAIL_VRF_TEMPLATE_TXT, link = link, name = recipient_name)
    sendEmailAsync(msg)