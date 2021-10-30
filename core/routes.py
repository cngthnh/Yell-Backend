import re
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
        try:
            tokenDict = decode(token)
            if tokenDict[ISSUER_KEY] != YELL_ISSUER:
                return jsonify(message=INVALID_TOKEN_MESSAGE), 403
            if (tokenDict[API_TOKEN_TYPE]!=ACCESS_TOKEN_TYPE):
                return jsonify(message=ACCESS_TOKEN_REQUIRED_MESSAGE), 403

        except jwt.ExpiredSignatureError:
            return jsonify(message=EXPIRED_TOKEN_MESSAGE), 401
        except Exception:
            return jsonify(message=INVALID_TOKEN_MESSAGE), 403
        
        return func(*args, **kwargs, uid=tokenDict[API_UID])
    return tokenCheck

@app.route('/')
def homepage():
    return 'Yell by Yellion'

@app.route(AUTH_ENDPOINT, methods=['POST'])
def getToken():
    try:
        data = request.get_json()
        _uid = str(data[API_UID])
        _hash = str(data[API_HASH]).lower()
    except Exception:
        return jsonify(message=INVALID_CREDENTIALS_MESSAGE), 401

    if (not re.fullmatch(REGEX_UID, _uid)):
        return jsonify(message=INVALID_UID_MESSAGE), 400
    if (not re.fullmatch(REGEX_HASH, _hash)):
        return jsonify(message=INVALID_HASH_MESSAGE), 400

    try:
        if checkAccount(_uid, _hash):
            _accessTokenDict = {API_UID: _uid, API_TOKEN_TYPE: ACCESS_TOKEN_TYPE}
            _refreshTokenDict = {API_UID: _uid, API_TOKEN_TYPE: REFRESH_TOKEN_TYPE}
            return jsonify(
                        access_token=encode(_accessTokenDict, ACCESS_TOKEN_EXP_TIME),
                        refresh_token=encode(_refreshTokenDict)
                        ), 200
        return jsonify(message=INACTIVATED_ACCOUNT_MESSAGE), 401
    except Exception:
        return jsonify(message=INVALID_CREDENTIALS_MESSAGE), 401

@app.route(AUTH_ENDPOINT, methods=['GET'])
def refreshToken():
    try:
        token = request.headers['Authorization']
    except Exception:
        return jsonify(message=INVALID_TOKEN_MESSAGE), 403

    schema, token = token.split(maxsplit=1)
    if schema!='Bearer':
        return jsonify(message=INVALID_TOKEN_MESSAGE), 403

    # parse token => dict of info
    try:
        tokenDict = decode(token)
        if tokenDict[ISSUER_KEY] != YELL_ISSUER:
            return jsonify(message=INVALID_TOKEN_MESSAGE), 403
        if (tokenDict[API_TOKEN_TYPE]!=REFRESH_TOKEN_TYPE):
            return jsonify(message=REFRESH_TOKEN_REQUIRED_MESSAGE), 403
        
        _accessTokenDict = {API_UID: tokenDict[API_UID], API_TOKEN_TYPE: ACCESS_TOKEN_TYPE}
        return jsonify(access_token=encode(_accessTokenDict, ACCESS_TOKEN_EXP_TIME))

    except jwt.ExpiredSignatureError:
        return jsonify(message=EXPIRED_TOKEN_MESSAGE), 401
    except Exception:
        return jsonify(message=INVALID_TOKEN_MESSAGE), 403
    
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
        return jsonify(message=EXPIRED_TOKEN_MESSAGE), 401

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
        _uid = str(data[API_UID])
        _email = str(data[API_EMAIL])
        _hash = str(data[API_HASH]).lower()
        _name = str(data[API_NAME])
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    if (not re.fullmatch(REGEX_UID, _uid)):
        return jsonify(message=INVALID_UID_MESSAGE), 400
    if (not re.fullmatch(REGEX_EMAIL, _email)):
        return jsonify(message=INVALID_EMAIL_MESSAGE), 400
    if (not re.fullmatch(REGEX_HASH, _hash)):
        return jsonify(message=INVALID_HASH_MESSAGE), 400

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

    return jsonify(message=PENDING_VERIFICATION_MESSAGE), 200

@app.route(USERS_ENDPOINT, methods=['PATCH'])
@tokenRequired
def updateAccount(uid):
    try:
        data = request.get_json()
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    fields = data.keys()
    
    if (not re.fullmatch(REGEX_UID, uid)):
            return jsonify(message=INVALID_UID_MESSAGE), 400
    user = db.session.query(UserAccount).filter_by(id=uid).first()
    if (user is None):
        return jsonify(message=USER_DOES_NOT_EXISTS_MESSAGE), 404

    emailChanged = False
    try:
        if (API_EMAIL in fields):
            user.email = str(data[API_EMAIL])
            if (not re.fullmatch(REGEX_EMAIL, user.email)):
                return jsonify(message=INVALID_EMAIL_MESSAGE), 400
            user.confirmed = False
            emailChanged = True
        if (API_NAME in fields):
            user.name = str(data[API_NAME])
        if (API_HASH in fields):
            user.hash = str(data[API_HASH])
            if (not re.fullmatch(REGEX_HASH, user.hash)):
                return jsonify(message=INVALID_HASH_MESSAGE), 400
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    try:
        user.updated_at = datetime.utcnow()
        db.session.add(user)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        print(str(e))
        sys.stdout.flush()
        return jsonify(message=FAILED_MESSAGE), 400

    if emailChanged:
        sendVerificationEmail(user.email, encode({API_UID: uid, API_EMAIL: user.email}, EMAIL_VERIFICATION_TIME), user.name)
        return jsonify(message=PENDING_VERIFICATION_MESSAGE), 200

    return jsonify(message=SUCCEED_MESSAGE), 200

@app.route(USERS_ENDPOINT, methods=['DELETE'])
@tokenRequired
def deleteAccount(uid):
    if (not re.fullmatch(REGEX_UID, uid)):
            return jsonify(message=INVALID_UID_MESSAGE), 400
    user = db.session.query(UserAccount).filter_by(id=uid).first()
    if (user is None):
        return jsonify(message=USER_DOES_NOT_EXISTS_MESSAGE), 404

    try:
        db.session.remove(user)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        print(str(e))
        sys.stdout.flush()
        return jsonify(message=FAILED_MESSAGE), 400

    return jsonify(message=SUCCEED_MESSAGE), 200

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
        _name = str(data[API_NAME])
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    dashboard = Dashboard(_name)
    permission = DashboardPermission(dashboard, ADMIN_ROLE)

    currentUser = db.session.query(UserAccount).filter_by(id=uid).first()
    currentUser.dashboards.append(permission)

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
        _name = str(data[API_NAME])
        _dashboardId = str(data[API_DASHBOARD_ID])
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    permissionCheck = db.session.query(DashboardPermission). \
        filter_by(user_id=uid, dashboard_id=_dashboardId).first()
    
    if (permissionCheck is None):
        return jsonify(message=FORBIDDEN_MESSAGE), 403

    if (EDIT_PERMISSION not in DASHBOARD_PERMISSION[permissionCheck.role]):
        return jsonify(message=FORBIDDEN_MESSAGE), 403

    currentDashboard = db.session.query(Dashboard).filter_by(id=_dashboardId).first()

    if (currentDashboard is None):
        return jsonify(message=INVALID_DASHBOARD_MESSAGE), 403

    task = Task(_name,
                _dashboardId)
    
    fields = data.keys()
    try:
        if (API_STATUS in fields):
            task.status = int(data[API_STATUS])
        if (API_NOTI_LEVEL in fields):
            task.notification_level = int(data[API_NOTI_LEVEL])
        if (API_PRIORITY in fields):
            task.priority = int(data[API_PRIORITY])
        if (API_PARENT_ID in fields):
            task.parent_id = str(data[API_PARENT_ID])
        if (API_START_TIME in fields):
            task.start_time = datetime.fromisoformat(str(data[API_START_TIME]))
        if (API_END_TIME in fields):
            task.end_time = datetime.fromisoformat(str(data[API_END_TIME]))
        if (API_LABELS in fields):
            task.labels = str(data[API_LABELS])
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    try:
        currentDashboard.tasks.append(task)
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
        _taskId = str(data[API_TASK_ID])
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400
    
    task = db.session.query(Task).filter(Task.id==_taskId).first()

    if (task is None):
        return jsonify(message=TASK_DOES_NOT_EXISTS_MESSAGE), 404

    permissionCheck = db.session.query(DashboardPermission). \
        filter_by(user_id=uid, dashboard_id=task.dashboard_id).first()
    
    if (permissionCheck is None):
        return jsonify(message=FORBIDDEN_MESSAGE), 403

    if (EDIT_PERMISSION not in DASHBOARD_PERMISSION[permissionCheck.role]):
        return jsonify(message=FORBIDDEN_MESSAGE), 403

    fields = data.keys()

    try:
        if API_NAME in fields:
            task.name = str(data[API_NAME])
        if API_STATUS in fields:
            task.status = int(data[API_STATUS])
        if API_NOTI_LEVEL in fields:
            task.notification_level = int(data[API_NOTI_LEVEL])
        if API_PRIORITY in fields:
            task.priority = int(data[API_PRIORITY])
        if API_PARENT_ID in fields:
            task.parent_id = str(data[API_PARENT_ID])
        if API_START_TIME in fields:
            task.start_time = datetime.fromisoformat(data[API_START_TIME])
        if API_END_TIME in fields:
            task.end_time = datetime.fromisoformat(data[API_END_TIME])
        if API_LABELS in fields:
            task.labels = str(data[API_LABELS])
        if API_DASHBOARD_ID in fields:
            task.dashboard_id = str(data[API_DASHBOARD_ID])
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400

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
        dashboard_id = str(request.args[API_DASHBOARD_ID])
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    permissionCheck = db.session.query(DashboardPermission). \
        filter_by(user_id=uid, dashboard_id=dashboard_id).first()
    
    if (permissionCheck is None):
        return jsonify(message=FORBIDDEN_MESSAGE), 403

    if (VIEW_PERMISSION not in DASHBOARD_PERMISSION[permissionCheck.role]):
        return jsonify(message=FORBIDDEN_MESSAGE), 403

    dashboard = db.session.query(Dashboard).filter_by(id=dashboard_id).first()

    if dashboard is None:
        return jsonify(message=DASHBOARD_DOES_NOT_EXISTS_MESSAGE), 404

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

    permissionCheck = db.session.query(DashboardPermission). \
        filter_by(user_id=uid, dashboard_id=_dashboardId).first()
    
    if (permissionCheck is None):
        return jsonify(message=FORBIDDEN_MESSAGE), 403

    if (EDIT_PERMISSION not in DASHBOARD_PERMISSION[permissionCheck.role]):
        return jsonify(message=FORBIDDEN_MESSAGE), 403

    dashboard = db.session.query(Dashboard).filter_by(id=_dashboardId).first()

    if (dashboard is None):
        return jsonify(message=FORBIDDEN_MESSAGE), 400
    
    fields = data.keys()
    
    if API_NAME in fields:
        dashboard.name = str(data[API_NAME])
    
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
        _dashboardId = str(data[API_DASHBOARD_ID])
        _targetUserId = str(data[API_UID])
        _role = str(data[API_ROLE])
        if _role not in DASHBOARD_ROLES:
            raise Exception()
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    permissionCheck = db.session.query(DashboardPermission). \
        filter_by(user_id=uid, dashboard_id=_dashboardId).first()
    
    if (permissionCheck is None):
        return jsonify(message=FORBIDDEN_MESSAGE), 403

    if (INVITE_PERMISSION not in DASHBOARD_PERMISSION[permissionCheck.role]):
        return jsonify(message=FORBIDDEN_MESSAGE), 403
    
    alreadyConfirmed = db.session.query(DashboardPermission).filter_by(dashboard_id=_dashboardId, user_id=_targetUserId).first()

    # Already have permission in this dashboard
    if (alreadyConfirmed is not None):
        alreadyConfirmed.role = _role
        alreadyConfirmed.updated_at = datetime.utcnow()
        try:
            db.session.add(alreadyConfirmed)
            db.session.commit()
        except SQLAlchemyError as e:
            print(str(e))
            sys.stdout.flush()
            db.session.rollback()
            return jsonify(message=FAILED_MESSAGE), 400
        return jsonify(message=SUCCEED_MESSAGE), 200

    dashboard = db.session.query(Dashboard).filter_by(id=_dashboardId).first()

    if (dashboard is None):
        return jsonify(message=FORBIDDEN_MESSAGE), 400

    targetUser = db.session.query(UserAccount).filter_by(id=_targetUserId).first()

    if (targetUser is None):
        return jsonify(message=USER_DOES_NOT_EXISTS_MESSAGE), 404

    sendDashboardInvitation(encode({API_UID: _targetUserId, 
                                    API_DASHBOARD_ID: _dashboardId, 
                                    API_INVITED_BY: uid,
                                    API_ROLE: _role}), 
                            targetUser.email, targetUser.name, dashboard.name)
    return jsonify(message=INVITATION_SENT_MESSAGE), 200

@app.route(DASHBOARDS_PERMISSION_ENDPOINT, methods=['DELETE'])
@tokenRequired
def removeDashboardPermission(uid):
    try:
        data = request.get_json()
        _dashboardId = str(data[API_DASHBOARD_ID])
        _targetUserId = str(data[API_UID])
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    permissionCheck = db.session.query(DashboardPermission). \
        filter_by(user_id=uid, dashboard_id=_dashboardId).first()
    
    if (permissionCheck is None):
        return jsonify(message=FORBIDDEN_MESSAGE), 403

    if (INVITE_PERMISSION not in DASHBOARD_PERMISSION[permissionCheck.role]):
        return jsonify(message=FORBIDDEN_MESSAGE), 403
    
    permissionCheck = db.session.query(DashboardPermission). \
        filter_by(user_id=_targetUserId, dashboard_id=_dashboardId).first()
    
    if (permissionCheck is None):
        return jsonify(message=FORBIDDEN_MESSAGE), 403

    targetUser = db.session.query(UserAccount).filter_by(id=_targetUserId).first()

    if (targetUser is None):
        return jsonify(message=USER_DOES_NOT_EXISTS_MESSAGE), 404
    
    targetUser.dashboards.remove(permissionCheck)

    try:
        db.session.add(targetUser)
        db.session.commit()
    except SQLAlchemyError:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return jsonify(message=FAILED_MESSAGE), 400

    return jsonify(message=SUCCEED_MESSAGE), 200

@app.route(DASHBOARD_INVITATION_ENDPOINT, methods=['GET'])
def confirmDashboardInvitation(token):
    if not verifyToken(token):
        return jsonify(message=INVALID_TOKEN_MESSAGE), 403

    try:
        tokenDict = decode(token)
    except jwt.ExpiredSignatureError:
        return jsonify(message=EXPIRED_TOKEN_MESSAGE), 401

    try:
        dashboard = db.session.query(Dashboard).filter_by(id=tokenDict[API_DASHBOARD_ID]).first()
        user = db.session.query(UserAccount).filter_by(id=tokenDict[API_UID]).first()
        permission = DashboardPermission(dashboard, tokenDict[API_ROLE])
        permission.user_id = tokenDict[API_UID]
        user.dashboards.append(permission)
    except Exception as e:
        print(str(e))
        sys.stdout.flush()
        return jsonify(message=INVALID_DATA_MESSAGE), 400
    
    try:
        db.session.add(user)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return jsonify(message=FAILED_MESSAGE), 400
    
    return jsonify(message=SUCCEED_MESSAGE), 200

@app.route(DASHBOARDS_ENDPOINT, methods=['DELETE'])
@tokenRequired
def deleteDashboard(uid):
    try:
        data = request.get_json()
        _dashboardId = str(data[API_DASHBOARD_ID])
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    permissionCheck = db.session.query(DashboardPermission). \
        filter_by(user_id=uid, dashboard_id=_dashboardId).first()
    
    if (permissionCheck is None):
        return jsonify(message=FORBIDDEN_MESSAGE), 403

    if (DELETE_PERMISSION not in DASHBOARD_PERMISSION[permissionCheck.role]):
        return jsonify(message=FORBIDDEN_MESSAGE), 403
    
    dashboard = db.session.query(Dashboard).filter_by(id=_dashboardId).first()

    if (dashboard is None):
        return jsonify(message=FORBIDDEN_MESSAGE), 400

    try:
        db.session.delete(dashboard)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return jsonify(message=FAILED_MESSAGE), 400
    
    return jsonify(message=SUCCEED_MESSAGE), 200

@app.route(TASKS_ENDPOINT, methods=['GET'])
@tokenRequired
def getTask(uid):
    try:
        _taskId = str(request.args[API_TASK_ID])
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400
    
    task = db.session.query(Task).filter(Task.id==_taskId).first()

    if (task is None):
        return jsonify(message=TASK_DOES_NOT_EXISTS_MESSAGE), 404

    permissionCheck = db.session.query(DashboardPermission). \
        filter_by(user_id=uid, dashboard_id=task.dashboard_id).first()
    
    if (permissionCheck is None):
        return jsonify(message=FORBIDDEN_MESSAGE), 403

    if (VIEW_PERMISSION not in DASHBOARD_PERMISSION[permissionCheck.role]):
        return jsonify(message=FORBIDDEN_MESSAGE), 403

    return jsonify(task.dict()), 200

@app.route(TASKS_ENDPOINT, methods=['DELETE'])
@tokenRequired
def deleteTask(uid):
    try:
        data = request.get_json()
        _taskId = str(data[API_TASK_ID])
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400
    
    task = db.session.query(Task).filter(Task.id==_taskId).first()
    
    if (task is None):
        return jsonify(message=TASK_DOES_NOT_EXISTS_MESSAGE), 404

    permissionCheck = db.session.query(DashboardPermission). \
        filter_by(user_id=uid, dashboard_id=task.dashboard_id).first()
    
    if (permissionCheck is None):
        return jsonify(message=FORBIDDEN_MESSAGE), 403

    if (EDIT_PERMISSION not in DASHBOARD_PERMISSION[permissionCheck.role]):
        return jsonify(message=FORBIDDEN_MESSAGE), 403

    try:
        db.session.delete(task)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return jsonify(message=FAILED_MESSAGE), 400

    return jsonify(message=SUCCEED_MESSAGE), 200

@app.route(FUNDS_ENDPOINT, methods=['POST'])
@tokenRequired
def createFund(uid):
    try:
        data = request.get_json()
        name = str(data[API_NAME])
        balance = int(data[API_BALANCE])
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    fund = Fund(uid, 
                name, 
                balance)
    
    fields = data.keys()

    try:
        if (API_START_TIME in fields):
            fund.start_time = datetime.fromisoformat(str(data[API_START_TIME]))
        if (API_END_TIME in fields):
            fund.end_time = datetime.fromisoformat(str(data[API_END_TIME]))
        if (API_THRESHOLD in fields):
            fund.threshold = datetime.fromisoformat(str(data[API_THRESHOLD]))
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    try:
        db.session.add(fund)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return jsonify(message=FAILED_MESSAGE), 400
    
    return jsonify(message=SUCCEED_MESSAGE, fund_id=fund.id), 200

@app.route(FUNDS_ENDPOINT, methods=['GET'])
@tokenRequired
def getFund(uid):
    try:
        _fundId = str(request.args[API_FUND_ID])
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400
    
    fund = db.session.query(Fund).filter_by(owner_id=uid, id=_fundId).first()

    if fund is None:
        return jsonify(message=FUND_DOES_NOT_EXISTS_MESSAGE), 404

    fetchType = request.args.get(API_FETCH)
    if (fetchType==API_FULL):
        return jsonify(fund.dict()), 200
    elif (fetchType==API_COMPACT):
        return jsonify(fund.compactDict()), 200
    else:
        return jsonify(fund.compactDict()), 200

@app.route(FUNDS_ENDPOINT, methods=['PATCH'])
@tokenRequired
def updateFund(uid):
    try:
        data = request.get_json()
        _fundId = str(data[API_FUND_ID])
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400
    
    fund = db.session.query(Fund).filter_by(id=_fundId, owner_id=uid).first()

    fields = data.keys()

    try:
        if API_NAME in fields:
            fund.name = str(data[API_NAME])
        if API_BALANCE in fields:
            fund.balance = int(data[API_BALANCE])
        if API_START_TIME in fields:
            fund.start_time = datetime.fromisoformat(data[API_START_TIME])
        if API_END_TIME in fields:
            fund.end_time = datetime.fromisoformat(data[API_END_TIME])
        if API_THRESHOLD in fields:
            fund.threshold = int(data[API_THRESHOLD])
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400
    
    fund.updated_at = datetime.utcnow()

    try:
        db.session.add(fund)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return jsonify(message=FAILED_MESSAGE), 400
    
    return jsonify(message=SUCCEED_MESSAGE), 200

@app.route(FUNDS_ENDPOINT, methods=['DELETE'])
@tokenRequired
def deleteFund(uid):
    try:
        data = request.get_json()
        _fundId = str(data[API_FUND_ID])
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400
    
    fund = db.session.query(Fund).filter_by(id=_fundId, owner_id=uid).first()

    if (fund is None):
        return jsonify(message=FUND_DOES_NOT_EXISTS_MESSAGE), 404

    try:
        db.session.delete(fund)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return jsonify(message=FAILED_MESSAGE), 400
    
    return jsonify(message=SUCCEED_MESSAGE), 200

@app.route(TRANSACTIONS_ENDPOINT, methods=['POST'])
@tokenRequired
def createTransaction(uid):
    try:
        data = request.get_json()
        amount = int(data[API_AMOUNT])
        fundId = str(data[API_FUND_ID])
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400
    
    currentFund = db.session.query(Fund).filter_by(id=fundId, owner_id=uid).first()
    if (currentFund is None):
        return jsonify(message=FORBIDDEN_MESSAGE), 403

    transaction = Transaction(fundId, amount)

    fields = data.keys()
    try:
        if (API_PURPOSES in fields):
            transaction.purposes = str(data[API_PURPOSES])
        if (API_TIME in fields):
            transaction.time = datetime.fromisoformat(str(data[API_TIME]))
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    try:
        currentFund.transactions.append(transaction)
        db.session.add(currentFund)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return jsonify(message=FAILED_MESSAGE), 400
    
    return jsonify(message=SUCCEED_MESSAGE, transaction_id=transaction.id), 200

@app.route(TRANSACTIONS_ENDPOINT, methods=['GET'])
@tokenRequired
def getTransaction(uid):
    try:
        transactionId = str(request.args[API_TRANSACTION_ID])
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400
    
    transaction = db.session.query(Transaction).filter_by(id=transactionId).first()
    if (transaction is None):
        return jsonify(message=TRANSACTION_DOES_NOT_EXISTS_MESSAGE), 404

    permissionCheck = db.session.query(Fund).join(UserAccount.funds).\
        filter(Fund.id==transaction.fund_id, UserAccount.id==uid).first()
    if permissionCheck is None:
        return jsonify(message=FORBIDDEN_MESSAGE), 403

    return jsonify(transaction.dict()), 200

@app.route(TRANSACTIONS_ENDPOINT, methods=['PATCH'])
@tokenRequired
def updateTransaction(uid):
    try:
        data = request.get_json()
        transactionId = str(data[API_TRANSACTION_ID])
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400
    
    transaction = db.session.query(Transaction).filter_by(id=transactionId).first()
    if (transaction is None):
        return jsonify(message=TRANSACTION_DOES_NOT_EXISTS_MESSAGE), 404

    permissionCheck = db.session.query(Fund).join(UserAccount.funds).\
        filter(Fund.id==transaction.fund_id, UserAccount.id==uid).first()
    if permissionCheck is None:
        return jsonify(message=FORBIDDEN_MESSAGE), 403

    try:
        fields = data.keys()
        if API_PURPOSES in fields:
            transaction.purposes = str(data[API_PURPOSES])
        if API_TIME in fields:
            transaction.time = datetime.fromisoformat(data[API_TIME])
        if API_AMOUNT in fields:
            transaction.amount = int(data[API_AMOUNT])
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400
    
    transaction.updated_at = datetime.utcnow()

    try:
        db.session.add(transaction)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return jsonify(message=FAILED_MESSAGE), 400
    
    return jsonify(message=SUCCEED_MESSAGE), 200

@app.route(TRANSACTIONS_ENDPOINT, methods=['DELETE'])
@tokenRequired
def deleteTransaction(uid):
    try:
        data = request.get_json()
        transactionId = str(data[API_TRANSACTION_ID])
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400
    
    transaction = db.session.query(Transaction).filter_by(id=transactionId).first()
    if (transaction is None):
        return jsonify(message=TRANSACTION_DOES_NOT_EXISTS_MESSAGE), 404

    permissionCheck = db.session.query(Fund).join(UserAccount.funds).\
        filter(Fund.id==transaction.fund_id, UserAccount.id==uid).first()
    if permissionCheck is None:
        return jsonify(message=FORBIDDEN_MESSAGE), 403
    
    try:
        db.session.delete(transaction)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return jsonify(message=FAILED_MESSAGE), 400
    
    return jsonify(message=SUCCEED_MESSAGE), 200