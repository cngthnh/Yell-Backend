from sqlalchemy.exc import SQLAlchemyError
from .cipher import *
from flask import request, jsonify
from .loader import *
from functools import wraps
from .email import sendVerificationEmail

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

@app.route(AUTH_ENDPOINT, methods=['POST'])
def getToken():
    _uid = request.form.get(API_UID)
    _hash = request.form.get(API_HASH)

    if (_uid is None or _hash is None):
        return jsonify(message=INVALID_CREDENTIALS_MESSAGE), 403

    try:
        if checkAccount(_uid, _hash):
            _tokenDict = {API_UID: _uid, API_HASH: _hash}
            return jsonify(token=generateToken(_tokenDict).decode('UTF-8'))
        return jsonify(message=INACTIVATED_ACCOUNT_MESSAGE), 403
    except Exception:
        return jsonify(message=INVALID_CREDENTIALS_MESSAGE), 403

@app.route(AUTHORIZED_TEST_ENDPOINT, methods=['POST'])
@tokenRequired
def authorized():
    return jsonify(message='AUTHORIZED'), 200

@app.route(EMAIL_VRF_ENDPOINT + '<token>', methods=['GET'])
def verifyAccount(token):
    if not verifyToken(token):
        return jsonify(message=INVALID_TOKEN_MESSAGE), 403

    try:
        tokenDict = decode(token)
    except jwt.ExpiredSignatureError:
        return jsonify(message=EXPIRED_TOKEN_MESSAGE)

    try:
        result = changeAccountStatus(tokenDict[API_UID], tokenDict[API_EMAIL])
    except Exception as e:
        return jsonify(message='INVALID_TOKEN_MESSAGE'), 403
    if result == True:
        return jsonify(message=VERIFIED_MESSAGE), 200
    else:
        return jsonify(message=INVALID_TOKEN_MESSAGE), 403

@app.route(SIGNUP_ENDPOINT, methods=['POST'])
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

    sendVerificationEmail(_email, encode({'uid': _uid, 'email': _email}, EMAIL_VERIFICATION_TIME), _name)

    token = generateToken({API_UID: _uid, API_HASH: _hash}).decode('UTF-8')

    return jsonify(message=PENDING_VERIFICATION_MESSAGE, token = token), 200

@app.route(EMAIL_CHECK_ENDPOINT, methods=['POST'])
def checkEmailAvailability():

    if request.form.get(API_EMAIL) is None:
        return jsonify(message=INVALID_EMAIL_MESSAGE), 403

    if db.session.query(UserAccount.email).filter_by(email=request.form.get(API_EMAIL)).first() is None:
        return jsonify(message=OK_MESSAGE), 200

    return jsonify(message=INVALID_EMAIL_MESSAGE), 200

@app.route(UID_CHECK_ENDPOINT, methods=['POST'])
def checkUidAvailability():

    if request.form.get(API_UID) is None:
        return jsonify(message=INVALID_UID_MESSAGE), 403

    if db.session.query(UserAccount.id).filter_by(id=request.form.get(API_UID)).first() is None:
        return jsonify(message=OK_MESSAGE), 200

    return jsonify(message=INVALID_UID_MESSAGE), 200