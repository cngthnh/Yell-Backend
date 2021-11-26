from flask import request

from ..views.dashboard_view import genDashboardInfo
from ..loader import *
from ..utils.cipher import *
from ..utils.email import *
from ..models.utils import *
from .auth_controller import tokenRequired
from ..views.message_view import getMessage

@tokenRequired
def createDashboard(uid):
    try:
        data = request.get_json()
        _name = str(data[API_NAME])
    except Exception:
        return getMessage(INVALID_DATA_MESSAGE), 400

    dashboard = Dashboard(_name)
    permission = DashboardPermission(dashboard, ADMIN_ROLE)

    currentUser = db.session.query(UserAccount).filter_by(id=uid).first()
    currentUser.dashboards.append(permission)

    try:
        db.session.add(currentUser)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return getMessage(FAILED_MESSAGE), 400
    
    return getMessage(SUCCEED_MESSAGE, dashboard_id=dashboard.id), 201

@tokenRequired
def getDashboard(uid):
    try:
        dashboard_id = str(request.args[API_DASHBOARD_ID])
    except Exception:
        return getMessage(INVALID_DATA_MESSAGE), 400

    permissionCheck = db.session.query(DashboardPermission). \
        filter_by(user_id=uid, dashboard_id=dashboard_id).first()
    
    if (permissionCheck is None):
        return getMessage(FORBIDDEN_MESSAGE), 403

    if (VIEW_PERMISSION not in DASHBOARD_PERMISSION[permissionCheck.role]):
        return getMessage(FORBIDDEN_MESSAGE), 403

    dashboard = db.session.query(Dashboard).filter_by(id=dashboard_id).first()

    if dashboard is None:
        return getMessage(DASHBOARD_DOES_NOT_EXISTS_MESSAGE), 404

    fetchType = request.args.get(API_FETCH)
    
    if (fetchType==API_FULL):
        return genDashboardInfo(dashboard.dict()), 200
    elif (fetchType==API_COMPACT):
        return genDashboardInfo(dashboard.compactDict())
    else:
        return genDashboardInfo(dashboard.compactDict())

@tokenRequired
def updateDashboard(uid):
    try:
        data = request.get_json()
        _dashboardId = data[API_DASHBOARD_ID]
    except Exception:
        return getMessage(INVALID_DATA_MESSAGE), 400

    permissionCheck = db.session.query(DashboardPermission). \
        filter_by(user_id=uid, dashboard_id=_dashboardId).first()
    
    if (permissionCheck is None):
        return getMessage(FORBIDDEN_MESSAGE), 403

    if (EDIT_PERMISSION not in DASHBOARD_PERMISSION[permissionCheck.role]):
        return getMessage(FORBIDDEN_MESSAGE), 403

    dashboard = db.session.query(Dashboard).filter_by(id=_dashboardId).first()

    if (dashboard is None):
        return getMessage(FORBIDDEN_MESSAGE), 400
    
    fields = data.keys()
    
    if API_NAME in fields and data[API_NAME] is not None:
        dashboard.name = str(data[API_NAME])
    
    dashboard.updated_at = datetime.utcnow()

    try:
        db.session.add(dashboard)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return getMessage(FAILED_MESSAGE), 400
    
    return getMessage(SUCCEED_MESSAGE), 200

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
        return getMessage(INVALID_DATA_MESSAGE), 400

    permissionCheck = db.session.query(DashboardPermission). \
        filter_by(user_id=uid, dashboard_id=_dashboardId).first()
    
    if (permissionCheck is None):
        return getMessage(FORBIDDEN_MESSAGE), 403

    if (INVITE_PERMISSION not in DASHBOARD_PERMISSION[permissionCheck.role]):
        return getMessage(FORBIDDEN_MESSAGE), 403
    
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
            return getMessage(FAILED_MESSAGE), 400
        return getMessage(SUCCEED_MESSAGE), 200

    dashboard = db.session.query(Dashboard).filter_by(id=_dashboardId).first()

    if (dashboard is None):
        return getMessage(FORBIDDEN_MESSAGE), 400

    targetUser = db.session.query(UserAccount).filter_by(id=_targetUserId).first()

    if (targetUser is None):
        return getMessage(USER_DOES_NOT_EXISTS_MESSAGE), 404

    sendDashboardInvitation(encode({API_UID: _targetUserId, 
                                    API_DASHBOARD_ID: _dashboardId, 
                                    API_INVITED_BY: uid,
                                    API_ROLE: _role}), 
                            targetUser.email, targetUser.name, dashboard.name)
    return getMessage(INVITATION_SENT_MESSAGE), 200

@tokenRequired
def removeDashboardPermission(uid):
    try:
        data = request.get_json()
        _dashboardId = str(data[API_DASHBOARD_ID])
        _targetUserId = str(data[API_UID])
    except Exception:
        return getMessage(INVALID_DATA_MESSAGE), 400

    permissionCheck = db.session.query(DashboardPermission). \
        filter_by(user_id=uid, dashboard_id=_dashboardId).first()
    
    if (permissionCheck is None):
        return getMessage(FORBIDDEN_MESSAGE), 403

    if (INVITE_PERMISSION not in DASHBOARD_PERMISSION[permissionCheck.role]):
        return getMessage(FORBIDDEN_MESSAGE), 403
    
    permissionCheck = db.session.query(DashboardPermission). \
        filter_by(user_id=_targetUserId, dashboard_id=_dashboardId).first()
    
    if (permissionCheck is None):
        return getMessage(FORBIDDEN_MESSAGE), 403

    targetUser = db.session.query(UserAccount).filter_by(id=_targetUserId).first()

    if (targetUser is None):
        return getMessage(USER_DOES_NOT_EXISTS_MESSAGE), 404
    
    targetUser.dashboards.remove(permissionCheck)

    try:
        db.session.add(targetUser)
        db.session.commit()
    except SQLAlchemyError:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return getMessage(FAILED_MESSAGE), 400

    return getMessage(SUCCEED_MESSAGE), 200

def confirmDashboardInvitation(token):
    if not verifyToken(token):
        return getMessage(INVALID_TOKEN_MESSAGE), 403

    try:
        tokenDict = decode(token)
    except jwt.ExpiredSignatureError:
        return getMessage(EXPIRED_TOKEN_MESSAGE), 401

    try:
        dashboard = db.session.query(Dashboard).filter_by(id=tokenDict[API_DASHBOARD_ID]).first()
        user = db.session.query(UserAccount).filter_by(id=tokenDict[API_UID]).first()
        permission = DashboardPermission(dashboard, tokenDict[API_ROLE])
        permission.user_id = tokenDict[API_UID]
        user.dashboards.append(permission)
    except Exception as e:
        print(str(e))
        sys.stdout.flush()
        return getMessage(INVALID_DATA_MESSAGE), 400
    
    try:
        db.session.add(user)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return getMessage(FAILED_MESSAGE), 400
    
    return getMessage(SUCCEED_MESSAGE), 200

@tokenRequired
def deleteDashboard(uid):
    try:
        data = request.get_json()
        _dashboardId = str(data[API_DASHBOARD_ID])
    except Exception:
        return getMessage(INVALID_DATA_MESSAGE), 400

    permissionCheck = db.session.query(DashboardPermission). \
        filter_by(user_id=uid, dashboard_id=_dashboardId).first()
    
    if (permissionCheck is None):
        return getMessage(FORBIDDEN_MESSAGE), 403

    if (DELETE_PERMISSION not in DASHBOARD_PERMISSION[permissionCheck.role]):
        return getMessage(FORBIDDEN_MESSAGE), 403
    
    dashboard = db.session.query(Dashboard).filter_by(id=_dashboardId).first()

    if (dashboard is None):
        return getMessage(FORBIDDEN_MESSAGE), 400

    try:
        db.session.delete(dashboard)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return getMessage(FAILED_MESSAGE), 400
    
    return getMessage(SUCCEED_MESSAGE), 200