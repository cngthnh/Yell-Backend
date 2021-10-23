from sqlalchemy.exc import SQLAlchemyError
from .utils.cipher import *
from flask import request, jsonify
from .loader import *
from .database.models import *
from .database.utils import *
from functools import wraps
from .utils.email import sendVerificationEmail
import sys

def tokenRequired(func):
    @wraps(func)
    def tokenCheck(*args, **kwargs):
        try:
            token = request.headers['Authorization']
        except Exception:
            return jsonify(message=INVALID_TOKEN_MESSAGE), 403

        scheme, token = token.split(' ')
        if scheme!='Bearer':
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
        return jsonify(message=INVALID_CREDENTIALS_MESSAGE), 401

    try:
        if checkAccount(_uid, _hash):
            _tokenDict = {API_UID: _uid, API_HASH: _hash}
            return jsonify(token=generateToken(_tokenDict).decode('UTF-8'))
        return jsonify(message=INACTIVATED_ACCOUNT_MESSAGE), 401
    except Exception:
        return jsonify(message=INVALID_CREDENTIALS_MESSAGE), 401

@app.route(AUTHORIZED_TEST_ENDPOINT, methods=['POST'])
@tokenRequired
def authorized(uid):
    return jsonify(message='AUTHORIZED'), 200

@app.route(EMAIL_VRF_ENDPOINT, methods=['GET'])
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
    except SQLAlchemyError as e:
        db.session.rollback()
        print(str(e))
        sys.stdout.flush()
        return jsonify(message=FAILED_MESSAGE), 403

    sendVerificationEmail(_email, encode({'uid': _uid, 'email': _email}, EMAIL_VERIFICATION_TIME), _name)

    token = generateToken({API_UID: _uid, API_HASH: _hash}).decode('UTF-8')

    return jsonify(message=PENDING_VERIFICATION_MESSAGE, token = token), 201

@app.route(EMAIL_CHECK_ENDPOINT, methods=['GET'])
def checkEmailAvailability():
    try:
        _email = request.args[API_EMAIL]
    except Exception:
        return jsonify(message=INVALID_EMAIL_MESSAGE), 409

    if db.session.query(UserAccount.email).filter_by(email=_email).first() is None:
        return jsonify(message=OK_MESSAGE), 200

    return jsonify(message=INVALID_EMAIL_MESSAGE), 409

@app.route(UID_CHECK_ENDPOINT, methods=['GET'])
def checkUidAvailability():
    try:
        _uid = request.args[API_UID]
    except Exception:
        return jsonify(message=INVALID_EMAIL_MESSAGE), 409

    if db.session.query(UserAccount.id).filter_by(id=_uid).first() is None:
        return jsonify(message=OK_MESSAGE), 200

    return jsonify(message=INVALID_UID_MESSAGE), 409

@app.route(CREATE_DASHBOARD_ENDPOINT, methods=['POST'])
@tokenRequired
def createDashboard(uid):
    try:
        _name = request.form[API_NAME]
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 403

    dashboard = Dashboard(_name, uid)
    
    currentUser = db.session.query(UserAccount).filter_by(id=uid).first()
    currentUser.dashboards.append(dashboard)

    try:
        db.session.add(currentUser)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify(message=FAILED_MESSAGE), 403
    
    return jsonify(message=SUCCEED_MESSAGE, dashboard_id=dashboard.id), 201

@app.route(CREATE_TASK_ENDPOINT, methods=['POST'])
@tokenRequired
def createTask(uid):
    try:
        _name = request.form[API_NAME]
        _dashboardId = request.form[API_DASHBOARD_ID]
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 403

    currentDashboard = db.session.query(Dashboard).filter_by(id=_dashboardId, owner_id=uid).first()
    if (currentDashboard is None):
        return jsonify(message=INVALID_DASHBOARD_MESSAGE), 403

    task = Task(_name,
                _dashboardId,
                request.form.get(API_STATUS), 
                request.form.get(API_NOTI_LEVEL), 
                request.form.get(API_PRIORITY),
                request.form.get(API_PARENT_ID),
                request.form.get(API_START_TIME),
                request.form.get(API_END_TIME),
                request.form.get(API_LABELS))
    
    currentDashboard.tasks.append(task)

    try:
        db.session.add(currentDashboard)
        db.session.commit()
    except SQLAlchemyError:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return jsonify(message=FAILED_MESSAGE), 403
    
    return jsonify(message=SUCCEED_MESSAGE, task_id=task.id), 201

@app.route(UPDATE_TASK_ENDPOINT, methods=['POST'])
@tokenRequired
def updateTask(uid):
    try:
        _taskId = request.form[API_TASK_ID]
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 403

    task = db.session.query(Task).filter(Task.dashboard_id.in_(db.session.query(Dashboard.id).filter(Dashboard.owner_id==uid)), Task.id==_taskId).first()

    fields = request.form.keys()
    if API_NAME in fields:
        task.name = request.form[API_NAME]
    if API_STATUS in fields:
        task.status = request.form[API_STATUS]
    if API_NOTI_LEVEL in fields:
        task.notification_level = request.form[API_NOTI_LEVEL]
    if API_PRIORITY in fields:
        task.priority = request.form[API_PRIORITY]
    if API_PARENT_ID in fields:
        task.parent_id = request.form[API_PARENT_ID]
    if API_START_TIME in fields:
        task.start_time = request.form[API_START_TIME]
    if API_END_TIME in fields:
        task.end_time = request.form[API_END_TIME]
    if API_LABELS in fields:
        task.labels = request.form[API_LABELS]
    if API_DASHBOARD_ID in fields:
        task.dashboard_id = request.form[API_DASHBOARD_ID]

    try:
        db.session.add(task)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return jsonify(message=FAILED_MESSAGE), 403
    
    return jsonify(message=SUCCEED_MESSAGE), 200

@app.route(GET_USER_PROFILE_ENDPOINT, methods=['GET'])
@tokenRequired
def getUserProfile():
    pass

@app.route('/.well-known/pki-validation/3151765195121080605031DCC5DFFEE6.txt', methods=['GET'])
@tokenRequired
def sslVerify():
    return (open('3151765195121080605031DCC5DFFEE6.txt').read()), 200