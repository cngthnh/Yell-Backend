from flask import request

from ..views.notif_view import *
from ..loader import *
from ..models.utils import *
from .auth_controller import tokenRequired
from ..views.message_view import getMessage
from ..utils.definitions import NOTIF_TYPE_INVITED

@tokenRequired
def getNotifications(uid):
    limit = int(request.args.get(API_LIMIT, 0, type=int)) 

    if limit != 0:
        notifications = db.session.query(Notification).filter_by(user_id=uid).limit(limit).all()
    else:
        notifications = db.session.query(Notification).filter_by(user_id=uid).all()
    
    if notifications is None or len(notifications) == 0:
        return getMessage(message=NO_NOTIF_MESSAGE), 404
    
    return parseNotifications(notifications), 200
    
@tokenRequired
def confirmNotification(uid):
    try:
        data = request.get_json()
        _notifId = data[API_NOTIF_ID]
    except Exception:
        return getMessage(message=INVALID_DATA_MESSAGE), 400
    
    notification = db.session.query(Notification).filter_by(id=_notifId).first()
    if notification is None:
        return getMessage(message=INVALID_DATA_MESSAGE), 400
    
    if notification.user_id is None or notification.dashboard_id is None:
        try:
            db.session.delete(notification)
            db.commit()
        except SQLAlchemyError as e:
            print(str(e))
            sys.stdout.flush()
            db.session.rollback()
            return getMessage(message=FAILED_MESSAGE), 400
        return getMessage(message=INVALID_DATA_MESSAGE), 400 
    
    if notification.ntype != NOTIF_TYPE_INVITED:
        return getMessage(message=INVALID_DATA_MESSAGE), 400

    if notification.user_id != uid:
        return getMessage(message=FORBIDDEN_MESSAGE), 403

    if notification.role not in DASHBOARD_ROLES:
        return getMessage(message=INVALID_DATA_MESSAGE), 400
    
    try:
        dashboard = db.session.query(Dashboard).filter_by(id=notification.dashboard_id).first()
        user = db.session.query(UserAccount).filter_by(id=notification.user_id).first()
        if (dashboard is None or user is None):
            try:
                db.session.delete(notification)
                db.commit()
            except SQLAlchemyError as e:
                print(str(e))
                sys.stdout.flush()
                db.session.rollback()
                return getMessage(message=FAILED_MESSAGE), 400
            return getMessage(message=INVALID_DATA_MESSAGE), 400 
        otherUsers = db.session.query(DashboardPermission).filter_by(dashboard_id=notification.dashboard_id)
        permission = DashboardPermission(dashboard, notification.role)
        permission.user_id = notification.user_id
        user.dashboards.append(permission)
        notification.role = None
        notification.updated_at = datetime.utcnow()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        return getMessage(message=INVALID_DATA_MESSAGE), 400

    notifications = []
    for u in otherUsers:
        notif = Notification(u.user_id, NOTIF_TYPE_JOINED, JOINED_NOTIF_TEXT.format(user.id, dashboard.name))
        notifications.append(notif)
    
    try:
        db.session.bulk_save_objects(notifications)
        db.session.add(user)
        db.session.add(notification)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return getMessage(message=FAILED_MESSAGE), 400
    
    return getMessage(message=SUCCEED_MESSAGE), 200

@tokenRequired
def rejectNotification(uid):
    try:
        data = request.get_json()
        _notifId = data[API_NOTIF_ID]
    except Exception:
        return getMessage(message=INVALID_DATA_MESSAGE), 400
    
    notification = db.session.query(Notification).filter_by(id=_notifId).first()
    if notification is None:
        return getMessage(message=INVALID_DATA_MESSAGE), 400
    
    if notification.ntype != NOTIF_TYPE_INVITED:
        return getMessage(message=INVALID_DATA_MESSAGE), 400

    if notification.user_id != uid:
        return getMessage(message=FORBIDDEN_MESSAGE), 403

    if notification.role is None:
        return getMessage(message=INVALID_DATA_MESSAGE), 400
    
    notification.role = None
    try:
        db.session.add(notification)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return getMessage(message=FAILED_MESSAGE), 400
    
    return getMessage(message=SUCCEED_MESSAGE), 200

def changeReadStatus(uid, notifId, status):
    
    notification = db.session.query(Notification).filter_by(id=notifId).first()
    if notification is None:
        return getMessage(message=INVALID_DATA_MESSAGE), 400
    
    if notification.ntype != NOTIF_TYPE_INVITED:
        return getMessage(message=INVALID_DATA_MESSAGE), 400

    if notification.user_id != uid:
        return getMessage(message=FORBIDDEN_MESSAGE), 403
    
    notification.read = status
    notification.updated_at = datetime.utcnow()
    
    try:
        db.session.add(notification)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return getMessage(message=FAILED_MESSAGE), 400
    
    return getMessage(message=SUCCEED_MESSAGE), 200

@tokenRequired
def markAsRead(uid):
    try:
        data = request.get_json()
        _notifId = data[API_NOTIF_ID]
    except Exception:
        return getMessage(message=INVALID_DATA_MESSAGE), 400
    
    return changeReadStatus(uid, _notifId, True)
    
@tokenRequired
def markAsUnread(uid):
    try:
        data = request.get_json()
        _notifId = data[API_NOTIF_ID]
    except Exception:
        return getMessage(message=INVALID_DATA_MESSAGE), 400
    
    return changeReadStatus(uid, _notifId, False)
