from flask import request

from ..views.task_view import genTaskInfo
from ..loader import *
from ..utils.cipher import *
from ..utils.email import *
from ..models.utils import *
from .auth_controller import tokenRequired
from ..views.message_view import getMessage
from ..utils.s3 import S3Handler
import json

@tokenRequired
def createTask(uid):
    try:
        files = request.files
        data = json.loads(request.form['data'])
        _name = str(data[API_NAME])
        _dashboardId = str(data[API_DASHBOARD_ID])
    except Exception as e:
        print(str(e))
        sys.stdout.flush()
        return getMessage(message=INVALID_DATA_MESSAGE), 400

    permissionCheck = db.session.query(DashboardPermission). \
        filter_by(user_id=uid, dashboard_id=_dashboardId).first()
    
    if (permissionCheck is None):
        return getMessage(message=FORBIDDEN_MESSAGE), 403

    if (EDIT_PERMISSION not in DASHBOARD_PERMISSION[permissionCheck.role]):
        return getMessage(message=FORBIDDEN_MESSAGE), 403

    currentDashboard = db.session.query(Dashboard).filter_by(id=_dashboardId).first()

    if (currentDashboard is None):
        return getMessage(message=INVALID_DASHBOARD_MESSAGE), 403

    task = Task(_name,
                _dashboardId)

    task.id = uuid.uuid4()

    s3 = S3Handler()

    for k, v in zip(files.keys(), files.values()):
        fileName = TEMP_FOLDER + uuid.uuid4().hex
        v.save(fileName)
        if (os.path.getsize(fileName) > MAX_FILE_SIZE):
            return getMessage(message=FILE_TOO_LARGE_MESSAGE), 400
        s3.uploadAsync(fileName, str(task.id), k)
        if (task.files is not None):
            if (k not in task.files.split(',')):
                if (task.files != ''):
                    task.files += ',' + k
                else:
                    task.files += k
        else:
            task.files = k

    fields = data.keys()
    try:
        if (API_STATUS in fields and data[API_STATUS] is not None):
            task.status = int(data[API_STATUS])
        if (API_NOTI_LEVEL in fields and data[API_NOTI_LEVEL] is not None):
            task.notification_level = int(data[API_NOTI_LEVEL])
        if (API_PRIORITY in fields and data[API_PRIORITY] is not None):
            task.priority = int(data[API_PRIORITY])
        if (API_PARENT_ID in fields and data[API_PARENT_ID] is not None):
            parent = db.session.query(Task).filter_by(id=str(data[API_PARENT_ID])).first()
            if parent is not None:
                task.parent_id = str(data[API_PARENT_ID])
        if (API_START_TIME in fields and data[API_START_TIME] is not None):
            task.start_time = datetime.fromisoformat(str(data[API_START_TIME]))
        if (API_END_TIME in fields and data[API_END_TIME] is not None):
            task.end_time = datetime.fromisoformat(str(data[API_END_TIME]))
        if (API_LABELS in fields and data[API_LABELS] is not None):
            task.labels = str(data[API_LABELS])
        if (API_CONTENT in fields and data[API_CONTENT] is not None):
            task.content = str(data[API_CONTENT])
    except Exception as e:
        print(str(e))
        sys.stdout.flush()
        return getMessage(message=INVALID_DATA_MESSAGE), 400

    try:
        currentDashboard.tasks.append(task)
        db.session.add(currentDashboard)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        print(str(e))
        sys.stdout.flush()
        return getMessage(message=FAILED_MESSAGE), 400
    
    return getMessage(message=SUCCEED_MESSAGE, task_id=str(task.id)), 201

@tokenRequired
def updateTask(uid):
    try:
        files = request.files
        data = json.loads(request.form['data'])
        _taskId = str(data[API_TASK_ID])
    except Exception:
        return getMessage(message=INVALID_DATA_MESSAGE), 400
    
    task = db.session.query(Task).filter(Task.id==_taskId).first()

    if (task is None):
        return getMessage(message=TASK_DOES_NOT_EXISTS_MESSAGE), 404

    permissionCheck = db.session.query(DashboardPermission). \
        filter_by(user_id=uid, dashboard_id=task.dashboard_id).first()
    
    if (permissionCheck is None):
        return getMessage(message=FORBIDDEN_MESSAGE), 403

    if (EDIT_PERMISSION not in DASHBOARD_PERMISSION[permissionCheck.role]):
        return getMessage(message=FORBIDDEN_MESSAGE), 403

    s3 = S3Handler()

    for k, v in zip(files.keys(), files.values()):
        fileName = TEMP_FOLDER + uuid.uuid4().hex
        v.save(fileName)
        if (os.path.getsize(fileName) > MAX_FILE_SIZE):
            return getMessage(message=FILE_TOO_LARGE_MESSAGE), 400
        s3.uploadAsync(fileName, str(task.id), k)
        if (task.files is not None):
            if (k not in task.files.split(',')):
                if (task.files != ''):
                    task.files += ',' + k
                else:
                    task.files += k
        else:
            task.files = k

    fields = data.keys()

    try:
        if API_NAME in fields and data[API_NAME] is not None:
            task.name = str(data[API_NAME])
        if API_STATUS in fields and data[API_STATUS] is not None:
            task.status = int(data[API_STATUS])
        if API_NOTI_LEVEL in fields and data[API_NOTI_LEVEL] is not None:
            task.notification_level = int(data[API_NOTI_LEVEL])
        if API_PRIORITY in fields and data[API_PRIORITY] is not None:
            task.priority = int(data[API_PRIORITY])
        if API_PARENT_ID in fields and data[API_PARENT_ID] is not None:
            parent = db.session.query(Task).filter_by(id=str(data[API_PARENT_ID])).first()
            if parent is not None:
                task.parent_id = str(data[API_PARENT_ID])
        if API_START_TIME in fields and data[API_START_TIME] is not None:
            task.start_time = datetime.fromisoformat(data[API_START_TIME])
        if API_END_TIME in fields and data[API_END_TIME] is not None:
            task.end_time = datetime.fromisoformat(data[API_END_TIME])
        if API_LABELS in fields and data[API_LABELS] is not None:
            task.labels = str(data[API_LABELS])
        if API_CONTENT in fields and data[API_CONTENT] is not None:
            task.content = str(data[API_CONTENT])
        if API_DASHBOARD_ID in fields and data[API_DASHBOARD_ID] is not None:
            permissionCheck = db.session.query(DashboardPermission). \
                filter_by(user_id=uid, dashboard_id=data[API_DASHBOARD_ID]).first()

            if (permissionCheck is None):
                return getMessage(message=FORBIDDEN_MESSAGE), 403
            if (EDIT_PERMISSION not in DASHBOARD_PERMISSION[permissionCheck.role]):
                return getMessage(message=FORBIDDEN_MESSAGE), 403

            task.dashboard_id = str(data[API_DASHBOARD_ID])
        if API_DELETE_FILES in fields and data[API_DELETE_FILES] is not None:
            for file in data[API_DELETE_FILES]:
                s3.delete(str(task.id), file)
                task.files.replace(file, '')
                task.files.replace(',,')
    except Exception:
        return getMessage(message=INVALID_DATA_MESSAGE), 400

    task.updated_at = datetime.utcnow()

    try:
        db.session.add(task)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return getMessage(message=FAILED_MESSAGE), 400
    
    return getMessage(message=SUCCEED_MESSAGE), 200

@tokenRequired
def getTask(uid):
    try:
        _taskId = str(request.args[API_TASK_ID])
    except Exception:
        return getMessage(message=INVALID_DATA_MESSAGE), 400
    
    task = db.session.query(Task).filter(Task.id==_taskId).first()

    if (task is None):
        return getMessage(message=TASK_DOES_NOT_EXISTS_MESSAGE), 404

    permissionCheck = db.session.query(DashboardPermission). \
        filter_by(user_id=uid, dashboard_id=task.dashboard_id).first()
    
    if (permissionCheck is None):
        return getMessage(message=FORBIDDEN_MESSAGE), 403

    if (VIEW_PERMISSION not in DASHBOARD_PERMISSION[permissionCheck.role]):
        return getMessage(message=FORBIDDEN_MESSAGE), 403

    return genTaskInfo(task.dict()), 200

@tokenRequired
def deleteTask(uid):
    try:
        data = request.get_json()
        _taskId = str(data[API_TASK_ID])
    except Exception:
        return getMessage(message=INVALID_DATA_MESSAGE), 400
    
    task = db.session.query(Task).filter(Task.id==_taskId).first()
    
    if (task is None):
        return getMessage(message=TASK_DOES_NOT_EXISTS_MESSAGE), 404

    permissionCheck = db.session.query(DashboardPermission). \
        filter_by(user_id=uid, dashboard_id=task.dashboard_id).first()
    
    if (permissionCheck is None):
        return getMessage(message=FORBIDDEN_MESSAGE), 403

    if (EDIT_PERMISSION not in DASHBOARD_PERMISSION[permissionCheck.role]):
        return getMessage(message=FORBIDDEN_MESSAGE), 403

    s3 = S3Handler()
    for file in task.files.split(','):
        s3.delete(str(task.id), file)

    try:
        db.session.delete(task)
        db.session.commit()
    except SQLAlchemyError as e:
        print(str(e))
        sys.stdout.flush()
        db.session.rollback()
        return getMessage(message=FAILED_MESSAGE), 400

    return getMessage(message=SUCCEED_MESSAGE), 200