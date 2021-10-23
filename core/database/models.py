from sqlalchemy.exc import SQLAlchemyError
import sys
from ..utils.definitions import MAX_UID_LENGTH
from ..loader import db
import uuid
from sqlalchemy.dialects.postgresql import UUID

usersDashboards = db.Table('users_dashboards',
    db.Column('dashboard_id', UUID(as_uuid=True), db.ForeignKey('dashboard.id'), primary_key=True),
    db.Column('task_id', UUID(as_uuid=True), db.ForeignKey('task.id'), primary_key=True),
)

class UserAccount(db.Model):
    __tablename__ = 'user_account'
    id = db.Column(db.String(MAX_UID_LENGTH), primary_key=True)
    email = db.Column(db.Text, unique=True)
    name = db.Column(db.UnicodeText)
    hash = db.Column(db.String(64))
    confirmed = db.Column(db.Boolean)
    dashboards = db.relationship('Dashboard', backref='owner', lazy=True)
    funds = db.relationship('Fund', backref='owner', lazy=True)

    def __init__(self, id, email, name, hash):
        self.id = id
        self.email = email
        self.name = name
        self.hash = hash
        self.confirmed = False
    
    def json(self):
        jsonified = {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'dashboards': db.session.query(Dashboard.id).filter_by(owner_id=self.id).all(),
            'funds': db.session.query(Fund.id).filter_by(owner_id=self.id).all()
        }
        return jsonified

class Dashboard(db.Model):
    __tablename__ = 'dashboard'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = db.Column(db.UnicodeText)
    tasks = db.relationship('Task', 
            secondary=usersDashboards, 
            lazy='subquery',
            backref=db.backref('dashboards', lazy=True))
    owner_id = db.Column(db.String(MAX_UID_LENGTH), db.ForeignKey('user_account.id'), nullable=False)

    def __init__(self, name, owner_id):
        self.name = name
        self.owner_id = owner_id

class Task(db.Model):
    __tablename__ = 'task'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    parent_id = db.Column(UUID(as_uuid=True), db.ForeignKey('task.id'), nullable=True)
    children = db.relationship('Task',
                backref=db.backref('parent', remote_side=[id]))
    dashboard_id = db.Column(UUID(as_uuid=True), db.ForeignKey('dashboard.id'), nullable=False)
    status = db.Column(db.Integer, default = 0)
    notification_level = db.Column(db.Integer, default = 0)
    priority = db.Column(db.Integer, default = 0)
    name = db.Column(db.UnicodeText)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    labels = db.Column(db.String, nullable=True)

    def __init__(self, name, dashboard_id, status = None, notification_level = None, priority = None, parent_id=None, start_time=None, end_time=None, labels=None):
        self.name = name
        self.dashboard_id = dashboard_id
        if status is not None:
            self.status = int(status)
        if notification_level is not None:
            self.notification_level = int(notification_level)
        if priority is not None:
            self.priority = int(priority)
        if parent_id is not None:
            self.parent_id = parent_id
        if start_time is not None:
            self.start_time = start_time
        if end_time is not None:
            self.end_time = end_time
        if labels is not None:
            self.labels = labels

class Fund(db.Model):
    __tablename__ = 'fund'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    owner_id = db.Column(db.String(MAX_UID_LENGTH), db.ForeignKey('user_account.id'), nullable=False)
    name = db.Column(db.UnicodeText, nullable=False)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    balance = db.Column(db.BigInteger, nullable=False)
    threshold = db.Column(db.BigInteger, nullable=True)
    expenditures = db.relationship('Expenditure', backref='fund', lazy=True)

    def __init__(self, owner_id, name, balance, start_time=None, end_time=None, threshold=None):
        self.owner_id = owner_id
        self.name = name
        self.balance = balance
        if start_time is not None:
            self.start_time = start_time
        if end_time is not None:
            self.end_time = end_time
        if threshold is not None:
            self.threshold = threshold

class Expenditure(db.Model):
    __tablename__ = 'expenditure'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    fund_id = db.Column(UUID(as_uuid=True), db.ForeignKey('fund.id'), nullable=False)
    used_for = db.Column(db.UnicodeText, nullable=True)
    time = db.Column(db.DateTime, nullable=True)
    spending = db.Column(db.BigInteger, nullable=False)

    def __init__(self, fund_id, spending, used_for=None, time=None):
        self.fund_id = fund_id
        self.spending = spending
        if used_for is not None:
            self.used_for = used_for
        if time is not None:
            self.time = time
    
try:
    db.create_all()
    db.session.commit()
except Exception as e:
    print(str(e))
    sys.stdout.flush()
    db.session.rollback()