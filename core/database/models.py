from sqlalchemy.exc import SQLAlchemyError
import sys
from ..utils.definitions import *
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
    
    def dict(self):
        dashboardDetails = []
        fundDetails = []

        for dashboard in self.dashboards:
            dashboardDetails.append(dashboard.dict())

        for fund in self.funds:
            fundDetails.append(fund.dict())

        result = {
            API_UID: self.id,
            API_EMAIL: self.email,
            API_NAME: self.name,
            API_DASHBOARDS: dashboardDetails,
            API_FUNDS: fundDetails
        }
        return result

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
    
    def dict(self):
        taskDetails = []
        for task in self.tasks:
            taskDetails.append(task.dict())
        
        result = {
            API_DASHBOARD_ID: str(self.id),
            API_NAME: self.name,
            API_TASKS: taskDetails,
        }
        return result

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
    
    def dict(self):
        subtaskDetails = []
        for task in self.children:
            subtaskDetails.append(task.dict())

        result = {
            API_TASK_ID: str(self.id),
            API_SUBTASKS: subtaskDetails,
            API_DASHBOARD_ID: str(self.dashboard_id),
            API_STATUS: self.status,
            API_NOTI_LEVEL: self.notification_level,
            API_PRIORITY: self.priority,
            API_START_TIME: self.start_time,
            API_END_TIME: self.end_time,
            API_LABELS: self.labels
        }
        return result


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

    def dict(self):
        expenditureDetails = []

        for exp in self.expenditures:
            expenditureDetails.append(exp.dict())

        result = {
            API_FUND_ID: str(self.id),
            API_NAME: self.name,
            API_START_TIME: self.start_time,
            API_END_TIME: self.end_time,
            API_BALANCE: self.balance,
            API_THRESHOLD: self.threshold,
            API_EXPENDITURES: expenditureDetails
        }

        return result

class Expenditure(db.Model):
    __tablename__ = 'expenditure'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    fund_id = db.Column(UUID(as_uuid=True), db.ForeignKey('fund.id'), nullable=False)
    purposes = db.Column(db.UnicodeText, nullable=True)
    time = db.Column(db.DateTime, nullable=True)
    spending = db.Column(db.BigInteger, nullable=False)

    def __init__(self, fund_id, spending, used_for=None, time=None):
        self.fund_id = fund_id
        self.spending = spending
        if used_for is not None:
            self.used_for = used_for
        if time is not None:
            self.time = time
    
    def dict(self):
        result = {
            API_EXPENDITURE_ID: str(self.id),
            API_FUND_ID: str(self.fund_id),
            API_PURPOSES: self.purposes,
            API_TIME: self.time,
            API_SPENDING: self.spending
        }
        return result

try:
    db.create_all()
    db.session.commit()
except Exception as e:
    print(str(e))
    sys.stdout.flush()
    db.session.rollback()