from sqlalchemy.exc import SQLAlchemyError
from .utils.cipher import *
from flask import request, jsonify
from .loader import *
from .database.models import *
from .database.utils import *
from functools import wraps
from .utils.email import sendDashboardInvitation, sendVerificationEmail
import sys

def tokenRequired(func):
    @wraps(func)
    def tokenCheck(*args, **kwargs):
        try:
            token = request.headers['Authorization']
        except Exception:
            return jsonify(message=INVALID_TOKEN_MESSAGE), 403

        schema, token = token.split(maxsplit=1)
        if schema!='Bearer':
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
        data = request.get_json()
        _uid = data[API_UID]
        _hash = data[API_HASH]
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
    except Exception:
        return jsonify(message=INVALID_TOKEN_MESSAGE), 403
    if result == True:
        return jsonify(message=VERIFIED_MESSAGE), 200
    else:
        return jsonify(message=INVALID_TOKEN_MESSAGE), 403

@app.route(USERS_ENDPOINT, methods=['POST'])
def createAccount():
    try:
        data = request.get_json()
        _uid = data[API_UID]
        _email = data[API_EMAIL]
        _hash = data[API_HASH]
        _name = data[API_NAME]
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    user = UserAccount(_uid, _email, _name, _hash)
    db.session.add(user)

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        print(str(e))
        sys.stdout.flush()
        return jsonify(message=FAILED_MESSAGE), 400

    sendVerificationEmail(_email, encode({API_UID: _uid, API_EMAIL: _email}, EMAIL_VERIFICATION_TIME), _name)

    token = generateToken({API_UID: _uid, API_HASH: _hash}).decode('UTF-8')

    return jsonify(message=PENDING_VERIFICATION_MESSAGE, token = token), 201

@app.route(USERS_CHECK_ENDPOINT, methods=['GET'])
def checkAvailability():
    _email = request.args.get(API_EMAIL)
    _uid = request.args.get(API_UID)

    if (_email is None and _uid is None):
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    elif ((_email is not None) and (_uid is not None)):
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    elif (_uid is None):
        if db.session.query(UserAccount.email).filter_by(email=_email).first() is None:
            return jsonify(message=OK_MESSAGE), 200
        return jsonify(message=INVALID_EMAIL_MESSAGE), 409
    
    else:
        if db.session.query(UserAccount.id).filter_by(id=_uid).first() is None:
            return jsonify(message=OK_MESSAGE), 200
        return jsonify(message=INVALID_UID_MESSAGE), 409

@app.route(DASHBOARDS_ENDPOINT, methods=['POST'])
@tokenRequired
def createDashboard(uid):
    try:
        data = request.get_json()
        _name = data[API_NAME]
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    dashboard = Dashboard(_name, uid)
    
    currentUser = db.session.query(UserAccount).filter_by(id=uid).first()
    currentUser.dashboards.append(dashboard)

    try:
        db.session.add(currentUser)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify(message=FAILED_MESSAGE), 400
    
    return jsonify(message=SUCCEED_MESSAGE, dashboard_id=dashboard.id), 201

@app.route(TASKS_ENDPOINT, methods=['POST'])
@tokenRequired
def createTask(uid):
    try:
        data = request.get_json()
        _name = data[API_NAME]
        _dashboardId = data[API_DASHBOARD_ID]
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    currentDashboard = db.session.query(Dashboard).join(usersDashboards).join(UserAccount). \
                    filter(Dashboard.id==_dashboardId, UserAccount.id==uid).first()

    if (currentDashboard is None):
        return jsonify(message=INVALID_DASHBOARD_MESSAGE), 403

    task = Task(_name,
                _dashboardId,
                data.get(API_STATUS), 
                data.get(API_NOTI_LEVEL), 
                data.get(API_PRIORITY),
                data.get(API_PARENT_ID),
                data.get(API_START_TIME),
                data.get(API_END_TIME),
                data.get(API_LABELS))
    
    currentDashboard.tasks.append(task)

    try:
        db.session.add(currentDashboard)
        db.session.commit()
    except SQLAlchemyError:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return jsonify(message=FAILED_MESSAGE), 400
    
    return jsonify(message=SUCCEED_MESSAGE, task_id=task.id), 201

@app.route(TASKS_ENDPOINT, methods=['PATCH'])
@tokenRequired
def updateTask(uid):
    try:
        data = request.get_json()
        _taskId = data[API_TASK_ID]
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400
    
    task = db.session.query(Task).filter(Task.id==_taskId).first()

    permissionCheck = db.session.query(Dashboard).join(usersDashboards).join(UserAccount). \
        filter(UserAccount.id==uid, Dashboard.id==task.dashboard_id).first()
    
    if (permissionCheck is None):
        return jsonify(message=FORBIDDEN_MESSAGE), 403

    fields = data.keys()
    if API_NAME in fields:
        task.name = data[API_NAME]
    if API_STATUS in fields:
        task.status = data[API_STATUS]
    if API_NOTI_LEVEL in fields:
        task.notification_level = data[API_NOTI_LEVEL]
    if API_PRIORITY in fields:
        task.priority = data[API_PRIORITY]
    if API_PARENT_ID in fields:
        task.parent_id = data[API_PARENT_ID]
    if API_START_TIME in fields:
        task.start_time = data[API_START_TIME]
    if API_END_TIME in fields:
        task.end_time = data[API_END_TIME]
    if API_LABELS in fields:
        task.labels = data[API_LABELS]
    if API_DASHBOARD_ID in fields:
        task.dashboard_id = data[API_DASHBOARD_ID]

    task.updated_at = datetime.utcnow()

    try:
        db.session.add(task)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return jsonify(message=FAILED_MESSAGE), 400
    
    return jsonify(message=SUCCEED_MESSAGE), 200

@app.route(USERS_ENDPOINT, methods=['GET'])
@tokenRequired
def getUserProfile(uid):

    user = db.session.query(UserAccount).filter_by(id=uid).first()

    if (user is not None):
        fetchType = request.args.get(API_FETCH)

        if (fetchType==API_FULL):
            return jsonify(user.dict()), 200
        elif (fetchType==API_COMPACT):
            return jsonify(user.compactDict()), 200
        else:
            return jsonify(user.compactDict()), 200

    return jsonify(USER_DOES_NOT_EXISTS_MESSAGE), 404

@app.route(DASHBOARDS_ENDPOINT, methods=['GET'])
@tokenRequired
def getDashboard(uid):
    try:
        dashboard_id = request.args[API_DASHBOARD_ID]
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    dashboard = db.session.query(Dashboard).join(usersDashboards).join(UserAccount). \
        filter(UserAccount.id==uid, Dashboard.id==dashboard_id).first()

    if dashboard is None:
        return jsonify(DASHBOARD_DOES_NOT_EXISTS_MESSAGE), 404

    fetchType = request.args.get(API_FETCH)
    
    if (fetchType==API_FULL):
        return jsonify(dashboard.dict()), 200
    elif (fetchType==API_COMPACT):
        return jsonify(dashboard.compactDict())
    else:
        return jsonify(dashboard.compactDict())

@app.route(DASHBOARDS_ENDPOINT, methods=['PATCH'])
@tokenRequired
def updateDashboard(uid):
    try:
        data = request.get_json()
        _dashboardId = data[API_DASHBOARD_ID]
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    dashboard = db.session.query(Dashboard).join(usersDashboards).join(UserAccount). \
                    filter(Dashboard.id==_dashboardId, UserAccount.id==uid).first()

    if (dashboard is None):
        return jsonify(message=FORBIDDEN_MESSAGE), 400
    
    fields = data.keys()
    
    if API_NAME in fields:
        dashboard.name = data[API_NAME]
    
    dashboard.updated_at = datetime.utcnow()

    try:
        db.session.add(dashboard)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return jsonify(message=FAILED_MESSAGE), 400
    
    return jsonify(message=SUCCEED_MESSAGE), 200

@app.route(DASHBOARDS_PERMISSION_ENDPOINT, methods=['POST'])
@tokenRequired
def grantDashboardPermission(uid):
    try:
        data = request.get_json()
        _dashboardId = data[API_DASHBOARD_ID]
        _targetUserId = data[API_UID]
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    dashboard = db.session.query(Dashboard).join(usersDashboards).join(UserAccount). \
                    filter(Dashboard.id==_dashboardId, UserAccount.id==uid).first()

    if (dashboard is None):
        return jsonify(message=FORBIDDEN_MESSAGE), 400

    targetUser = db.session.query(UserAccount).filter_by(id=_targetUserId).first()

    if (targetUser is None):
        return jsonify(message=USER_DOES_NOT_EXISTS_MESSAGE), 404

    sendDashboardInvitation(encode({API_UID: _targetUserId, API_DASHBOARD_ID: dashboard.id, API_INVITED_BY: uid}), targetUser.email, targetUser.name, dashboard.name)
    return jsonify(message=INVITATION_SENT_MESSAGE), 200

@app.route(DASHBOARD_INVITATION_ENDPOINT, methods=['GET'])
def confirmDashboardInvitation():
    try:
        token = request.args[API_TOKEN]
    except Exception:
        return jsonify(INVALID_TOKEN_MESSAGE), 403

    if not verifyToken(token):
        return jsonify(message=INVALID_TOKEN_MESSAGE), 403

    try:
        tokenDict = decode(token)
    except jwt.ExpiredSignatureError:
        return jsonify(message=EXPIRED_TOKEN_MESSAGE)

    try:
        dashboard = db.session.query(Dashboard).filter_by(id=tokenDict[API_DASHBOARD_ID]).first()
        user = db.session.query(UserAccount).filter_by(id=tokenDict[API_UID]).first()
        user.dashboards.append(dashboard)
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400
    
    try:
        db.session.add(user)
        db.session.commit()
    except SQLAlchemyError:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return jsonify(message=FAILED_MESSAGE), 400
    
    return jsonify(message=SUCCEED_MESSAGE), 200
