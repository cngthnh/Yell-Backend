from flask_mail import Mail, Message
import os

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
    msg.html = open('email/email_template.html', 'r').read().format(token)
    mail.send(msg)