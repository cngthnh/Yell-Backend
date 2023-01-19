import os
from flask import Flask
from .utils.definitions import *
from .utils.email import mail
import secrets
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
import requests
import time
import json

def loadKeys():
    try:
        os.environ['YELL_ENC_KEY'] = open('enc','r').readline().strip()
        os.remove('enc')
        os.environ['YELL_SIG_KEY'] = open('sig','r').readline().strip()
        os.remove('sig')
    except Exception:
        pass

def loadEmailConfigs():
    try:
        os.environ['MAIL_USERNAME'] = (open('mail_username', 'r').readline()).strip()
        os.remove('mail_username')
        os.environ['MAIL_PASSWORD'] = (open('mail_password', 'r').readline()).strip()
        os.remove('mail_password')
    except Exception:
        pass

def loadUrl():
    try:
        os.environ['YELL_MAIN_URL'] = (open('main_url', 'r').readline()).strip()
        os.remove('main_url')
    except Exception:
        pass

def loadStorage():
    try:
        os.environ['AWS_ACCESS_KEY'] = (open('aws_access', 'r').readline()).strip()
        os.remove('aws_access')
        os.environ['AWS_SECRET_ACCESS_KEY'] = (open('aws_secret', 'r').readline()).strip()
        os.remove('aws_secret')
        os.environ['AWS_S3_BUCKET_NAME'] = (open('aws_s3_bucket', 'r').readline()).strip()
        os.remove('aws_s3_bucket')
        os.mkdir(TEMP_FOLDER)
    except Exception:
        pass

def loadConfigs():
    loadEmailConfigs()
    loadKeys()
    loadUrl()
    loadStorage()

# init Flask
app = Flask(__name__)
Talisman(app)

# load env
# loadConfigs()

# init SQL database and email connection
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL'].replace('postgres', 'postgresql+psycopg2')
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.yandex.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['DEBUG'] = True

# init DB
db = SQLAlchemy(app)

def heartbeater():
    try:
        while (True):
            for _ in range(HEARTBEAT_RETRIES):
                response = requests.post(os.environ['SERVICE_DISCOVERY_URL'], 
                    data = json.dumps({"name": "Yell API Service", "url": os.environ['YELL_MAIN_URL']}), 
                    headers = {'content-type': 'application/json'})
                if response.ok:
                    break
            time.sleep(HEARTBEAT_INTERVAL)
    except Exception as e:
        print(e)

with app.app_context():
    mail.init_app(app)