from flask_mail import Mail, Message
import os

import threading
from .definitions import *
from flask import render_template, copy_current_request_context

mail = Mail()

def sendEmailAsync(msg):
    @copy_current_request_context
    def sendMessage(msg):
        mail.send(msg)

    sender = threading.Thread(name='mail_sender', target=sendMessage, args=(msg,))
    sender.start()

def sendVerificationEmail(recipient, token, recipient_name, code):
    sender_mail = os.environ.get('MAIL_USERNAME')
    msg = Message(subject = 'Yell Account Verification', sender = ('Yell', sender_mail), recipients = [recipient])
    link = os.environ.get('YELL_MAIN_URL', '') + EMAIL_VRF_SIGNATURE + token
    msg.body = render_template(EMAIL_VRF_TEMPLATE_TXT, name = recipient_name, link = link, code = code)
    msg.html = render_template(EMAIL_VRF_TEMPLATE_HTML, link = link, name = recipient_name, mail = sender_mail, code = code)
    sendEmailAsync(msg)

def sendDashboardInvitation(token, recipient_email, recipient_name, dashboard_name):
    sender_mail = os.environ.get('MAIL_USERNAME')
    msg = Message(subject = 'Yell Dashboard Invitation', sender = ('Yell', sender_mail), recipients = [recipient_email])
    link = os.environ.get('YELL_MAIN_URL', '') + DASHBOARD_INVITATION_SIGNATURE + token
    msg.body = render_template(DASHBOARD_INV_TEMPLATE_TXT, link = link, recipient_name = recipient_name, dashboard_name = dashboard_name)
    sendEmailAsync(msg)

def sendPasswordChangeRequest(recipient, recipient_name, code):
    sender_mail = os.environ.get('MAIL_USERNAME')
    msg = Message(subject = 'Yell Password Change Confirmation', sender = ('Yell', sender_mail), recipients = [recipient])
    msg.body = render_template(EMAIL_VRF_TEMPLATE_TXT, name = recipient_name, code = code)
    msg.html = render_template(EMAIL_VRF_TEMPLATE_HTML, name = recipient_name, mail = sender_mail, code = code)
    sendEmailAsync(msg)