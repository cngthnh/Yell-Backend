from sqlalchemy.exc import SQLAlchemyError
from ..loader import db
import uuid
from sqlalchemy.dialects.postgresql import UUID

userTasks = db.Table('user_tasks',
    db.Column('user_id', db.String(64), db.ForeignKey('user_account.id'), primary_key=True),
    db.Column('task_id', UUID(as_uuid=True), db.ForeignKey('task.id'), primary_key=True),
)

class UserAccount(db.Model):
    __tablename__ = 'user_account'
    id = db.Column(db.String(64), primary_key=True)
    email = db.Column(db.Text, unique=True)
    name = db.Column(db.UnicodeText)
    hash = db.Column(db.String(64))
    confirmed = db.Column(db.Boolean)
    tasks = db.relationship('Task', 
            secondary=userTasks, 
            lazy='subquery',
            backref=db.backref('accounts', lazy=True))

    def __init__(self, id, email, name, hash):
        self.id = id
        self.email = email
        self.name = name
        self.hash = hash
        self.confirmed = False
    
class Task(db.Model):
    __tablename__ = 'task'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    parent_id = db.Column(UUID(as_uuid=True), db.ForeignKey('task.id'), nullable=True)
    children = db.relationship('Task',
                backref=db.backref('parent', remote_side=[id]))
    status = db.Column(db.String)
    notification_level = db.Column(db.Integer)
    priority = db.Column(db.Integer, default = 0)
    name = db.Column(db.UnicodeText)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    labels = db.Column(db.String, nullable=True)

    def __init__(self, name, status, notification_level, priority, parent_id=None, start_time=None, end_time=None, labels=None):
        self.name = name
        self.status = status
        self.notification_level = notification_level
        self.priority = priority
        if parent_id is not None:
            self.parent_id = parent_id
        if start_time is not None:
            self.start_time = start_time
        if end_time is not None:
            self.end_time = end_time
        if labels is not None:
            self.labels = labels

def checkAccount(uid, hash):
    result = db.session.query(UserAccount).filter_by(id = uid, hash = hash).first()
    if (result is None):
        return False
    if (result.confirmed == False):
        return False
    return True

def changeAccountStatus(uid, email):
    db.session.query(UserAccount).filter_by(id = uid, email = email).update({'confirmed': True})
    try:
        db.session.commit()
        return True
    except SQLAlchemyError:
        db.session.rollback()
        return False

try:
    db.create_all()
    db.session.commit()
except Exception as e:
    db.session.rollback()
    raise Exception(str(e))