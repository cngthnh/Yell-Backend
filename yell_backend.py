from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from utils.cipher import *
import os
from functools import wraps
import secrets
from utils.definitions import *
from database.utils import getDbUri, db
from database.models import *
from utils.email import sendVerificationEmail, mail
from utils.loader import loadConfigs

# init Flask
app = Flask(__name__)

# load env
loadConfigs()

# init SQL database and email connection
app.config['SQLALCHEMY_DATABASE_URI'] = getDbUri()
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER']='smtp-mail.outlook.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

with app.app_context():
    db.init_app(app)
    mail.init_app(app)

def tokenRequired(func):
    @wraps(func)
    def tokenCheck(*args, **kwargs):

        token = request.form.get(API_TOKEN)

        if token is None:
            return jsonify(message=INVALID_TOKEN_MESSAGE), 403

        # parse token => dict of info
        infoDict = parseToken(token)
        if infoDict is None:
            return jsonify(message=INVALID_TOKEN_MESSAGE), 403

        # check if account is valid in DB
        try:
            if not checkAccount(infoDict[API_UID], infoDict[API_HASH]):
                return jsonify(message=INVALID_TOKEN_MESSAGE), 403
        except Exception:
            return jsonify(message=INVALID_TOKEN_MESSAGE), 403

        return func(*args, **kwargs)
    return tokenCheck

@app.route('/')
def homepage():
    return 'Yell by Yellion'

@app.route('/api/auth', methods=['POST'])
def getToken():
    _uid = request.form.get(API_UID)
    _hash = request.form.get(API_HASH)

    if (_uid is None or _hash is None):
        return jsonify(message=INVALID_CREDENTIALS_MESSAGE), 403

    try:
        if checkAccount(_uid, _hash):
            _tokenDict = {API_UID: _uid, API_HASH: _hash}
            return jsonify(token=generateToken(_tokenDict).decode('UTF-8'))
        return jsonify(message=INVALID_CREDENTIALS_MESSAGE), 403
    except Exception:
        return jsonify(message=INVALID_CREDENTIALS_MESSAGE), 403

@app.route('/api/authorized', methods=['POST'])
@tokenRequired
def authorized():
    return jsonify(message='AUTHORIZED'), 200

@app.route('/api/account/verify/<token>', methods=['GET'])
def verifyEmail():
    pass

@app.route('/api/sign_up', methods=['POST'])
def createAccount():
    _uid = request.form.get(API_UID)
    _email = request.form.get(API_EMAIL)
    _hash = request.form.get(API_HASH)
    _name = request.form.get(API_USER_FULL_NAME)

    if (_uid is None or
        _hash is None or
        _email is None or
        _name is None):
        return jsonify(message=INVALID_DATA_MESSAGE), 403

    user = UserAccount(_uid, _email, _name, _hash)
    db.session.add(user)

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify(message=FAILED_MESSAGE), 403

    sendVerificationEmail(_email, encode({'uid': _uid}, EMAIL_VERIFICATION_TIME), _name)

    token = generateToken({API_UID: _uid, API_HASH: _hash}).decode('UTF-8')

    return jsonify(message=PENDING_VERIFICATION_MESSAGE, token = token), 200

@app.route('/api/email_check', methods=['POST'])
def checkEmailAvailability():

    if request.form.get(API_EMAIL) is None:
        return jsonify(message=INVALID_EMAIL_MESSAGE), 403

    if db.session.query(UserAccount.email).filter_by(email=request.form.get(API_EMAIL)).first() is None:
        return jsonify(message=OK_MESSAGE), 200

    return jsonify(message=INVALID_EMAIL_MESSAGE), 200

@app.route('/api/uid_check', methods=['POST'])
def checkUidAvailability():

    if request.form.get(API_UID) is None:
        return jsonify(message=INVALID_UID_MESSAGE), 403

    if db.session.query(UserAccount.id).filter_by(id=request.form.get(API_UID)).first() is None:
        return jsonify(message=OK_MESSAGE), 200

    return jsonify(message=INVALID_UID_MESSAGE), 200
    
if __name__ == '__main__':
    db.create_all()
    app.run(ssl_context='adhoc', host='0.0.0.0', port=os.environ.get('PORT', 80))