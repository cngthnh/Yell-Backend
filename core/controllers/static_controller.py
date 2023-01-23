from flask import request, Response, stream_with_context
from ..loader import *
from ..utils.cipher import *
from ..utils.email import *
from ..models.utils import *
from .auth_controller import tokenRequired
from ..views.message_view import getMessage
from ..utils.storage import StorageHandler

@tokenRequired
def getPrivateStaticResource(uid, category, entity, resource_name):
    isAttachment = request.args.get('is_attachment', 'false').lower() == 'true'
    if (category == 'task_attachments'):

        _taskId = entity

        task = db.session.query(Task).filter(Task.id==_taskId).first()

        if (task is None):
            return getMessage(message=TASK_DOES_NOT_EXISTS_MESSAGE), 404

        permissionCheck = db.session.query(DashboardPermission). \
            filter_by(user_id=uid, dashboard_id=task.dashboard_id).first()
        
        if (permissionCheck is None):
            return getMessage(message=FORBIDDEN_MESSAGE), 403

        if (EDIT_PERMISSION not in DASHBOARD_PERMISSION[permissionCheck.role]):
            return getMessage(message=FORBIDDEN_MESSAGE), 403

        fileMetadata = json.loads(task.files)
        mimeType = None
        contentLength = None
        if (resource_name in fileMetadata.keys()):
            mimeType = fileMetadata[resource_name]["mime"]
            contentLength = fileMetadata[resource_name]["size"]
        else:
            return getMessage(message=RESOURCE_DOES_NOT_EXISTS_MESSAGE), 404
        storage = StorageHandler()
        return Response(
            stream_with_context(storage.get(category, entity, resource_name)),
            headers={
                'Content-Disposition': f'attachment; filename={resource_name}' if isAttachment else f'inline; filename={resource_name}',
                'Content-Length': contentLength,
            }, 
            mimetype = mimeType
        )
    else:
        return getMessage(message=RESOURCE_DOES_NOT_EXISTS_MESSAGE), 404

def getPublicStaticResource(resource_name):
    isAttachment = request.args.get('is_attachment', 'false').lower() == 'true'
    storage = StorageHandler()
    mime = storage.getMime(resource_name)
    return Response(
        stream_with_context(storage.get(PUBLIC_FOLDER, resource_name)),
        headers={
            'Content-Disposition': f'attachment; filename={resource_name}' if isAttachment else f'inline; filename={resource_name}',
        },
        mimetype=mime
    )

def refreshPublicStaticResource():
    storage = StorageHandler()
    storage.uploadPublicFiles()
    return "OK", 200

