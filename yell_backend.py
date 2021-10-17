from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from cipher import *
import os
from functools import wraps
import secrets

from database.utils import getDbUri, db, loadDbConfigs
from database.models import *

# init Flask
app = Flask(__name__)

# load env
loadDbConfigs()
loadKeys()

# init SQL database connect
app.config['SQLALCHEMY_DATABASE_URI'] = getDbUri()
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

with app.app_context():
    db.init_app(app)

def tokenRequired(func):
    @wraps(func)
    def tokenCheck(*args, **kwargs):

        token = request.form.get('token')

        if token is None:
            return jsonify(message='INVALID_TOKEN'), 403

        if not accountCheck(token):
            return jsonify(message='INVALID_TOKEN'), 403

        return func(*args, **kwargs)
    return tokenCheck

@app.route('/')
def homepage():
    return 'Yell by Yellion'

@app.route('/api/auth', methods=['POST'])
def getToken():
    if (request.form.get('uid') is None or request.form.get('hash') is None):
        return jsonify(message='INVALID_CREDENTIALS'), 403
    try:
        _tokenDict = {'uid': request.form.get('uid'), 'hash': request.form.get('hash')}
        return generateToken(_tokenDict)
    except Exception:
        return jsonify(message='INVALID_CREDENTIALS'), 403

@app.route('/api/authorized', methods=['POST'])
@tokenRequired
def authorized():
    return jsonify(message='AUTHORIZED'), 200

@app.route('/api/sign_up', methods=['POST'])
def createAccount():
    if (request.form.get('uid') is None or
        request.form.get('hash') is None or
        request.form.get('email') is None or
        request.form.get('name') is None):
        return jsonify(message='INVALID_USER_INFOMATION'), 403

    uid = UserAccount(request.form.get('uid'), request.form.get('email'), request.form.get('name'), request.form.get('hash'))
    db.session.add(uid)

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify(message='FAILED'), 403

    return jsonify(message='SUCCESS'), 200

@app.route('/api/email_check', methods=['POST'])
def checkEmailAvailability():
    if request.form.get('email') is None:
        return jsonify(message='INVALID_EMAIL'), 403
    if db.session.query(UserAccount.email).filter_by(email=request.form.get('email')).first() is None:
        return jsonify(message='VALID_EMAIL'), 200
    return jsonify(message='INVALID_EMAIL'), 200

@app.route('/api/uid_check', methods=['POST'])
def checkUidAvailability():
    if request.form.get('uid') is None:
        return jsonify(message='INVALID_UID'), 403
    if db.session.query(UserAccount.id).filter_by(id=request.form.get('uid')).first() is None:
        return jsonify(message='VALID_UID'), 200
    return jsonify(message='INVALID_UID'), 200
    
if __name__ == '__main__':
    db.create_all()
    app.run(ssl_context='adhoc', host='0.0.0.0', port=os.environ.get('PORT', 80))