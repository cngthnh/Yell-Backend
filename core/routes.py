from sqlalchemy.exc import SQLAlchemyError
from .utils.cipher import *
from flask import request, jsonify
from .loader import *
from .database.models import *
from functools import wraps
from .utils.email import sendVerificationEmail

def tokenRequired(func):
    @wraps(func)
    def tokenCheck(*args, **kwargs):
        try:
            token = request.form[API_TOKEN]
        except Exception:
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

        return func(*args, **kwargs, uid=infoDict[API_UID])
    return tokenCheck

@app.route('/')
def homepage():
    return 'Yell by Yellion'

@app.route(AUTH_ENDPOINT, methods=['POST'])
def getToken():
    try:
        _uid = request.form[API_UID]
        _hash = request.form[API_HASH]
    except Exception:
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
def authorized(uid):
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
    try:
        _uid = request.form[API_UID]
        _email = request.form[API_EMAIL]
        _hash = request.form[API_HASH]
        _name = request.form[API_NAME]
    except Exception:
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
    try:
        _email = request.form[API_EMAIL]
    except Exception:
        return jsonify(message=INVALID_EMAIL_MESSAGE), 403

    if db.session.query(UserAccount.email).filter_by(email=_email).first() is None:
        return jsonify(message=OK_MESSAGE), 200

    return jsonify(message=INVALID_EMAIL_MESSAGE), 200

@app.route(UID_CHECK_ENDPOINT, methods=['POST'])
def checkUidAvailability():
    try:
        _uid = request.form[API_UID]
    except Exception:
        return jsonify(message=INVALID_EMAIL_MESSAGE), 403

    if db.session.query(UserAccount.id).filter_by(id=_uid).first() is None:
        return jsonify(message=OK_MESSAGE), 200

    return jsonify(message=INVALID_UID_MESSAGE), 200

@app.route(CREATE_TASK_ENDPOINT, methods=['POST'])
@tokenRequired
def createTask(uid):
    try:
        _name = request.form[API_NAME]
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 403

    task = Task(_name, 
                request.form.get(API_STATUS), 
                request.form.get(API_NOTI_LEVEL), 
                request.form.get(API_PRIORITY),
                request.form.get(API_PARENT_ID),
                request.form.get(API_START_TIME),
                request.form.get(API_END_TIME),
                request.form.get(API_LABELS))
    
    db.session.query(UserAccount.id).filter_by(id=uid).update({'tasks': UserAccount.tasks.append(task)})

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify(message=FAILED_MESSAGE), 403
    
    return jsonify(message=SUCCEED_MESSAGE), 200