from sqlalchemy.exc import SQLAlchemyError
import sys
from ..utils.definitions import *
from ..loader import db
import uuid
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

class DashboardPermission(db.Model):
    __tablename__ = 'dashboard_permission'
    user_id = db.Column(db.String(MAX_UID_LENGTH), db.ForeignKey('user_account.id'), primary_key=True)
    dashboard_id = db.Column(UUID(as_uuid=True), db.ForeignKey('dashboard.id'), primary_key=True)
    role = db.Column(db.String)
    dashboard = db.relationship('Dashboard', back_populates='users')
    user = db.relationship('UserAccount', back_populates='dashboards')

    def __init__(self, dashboard, role):
        self.dashboard = dashboard
        self.role = role

class UserAccount(db.Model):
    __tablename__ = 'user_account'
    id = db.Column(db.String(MAX_UID_LENGTH), primary_key=True)
    email = db.Column(db.Text, unique=True)
    name = db.Column(db.UnicodeText)
    hash = db.Column(db.String(64))
    confirmed = db.Column(db.Boolean)
    dashboards = db.relationship('DashboardPermission', back_populates='user')
    funds = db.relationship('Fund', backref='owner', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

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
            API_FUNDS: fundDetails,
            API_CREATED_AT: self.created_at.isoformat(),
            API_UPDATED_AT: self.updated_at.isoformat()
        }
        return result
    
    def compactDict(self):
        result = {
            API_UID: self.id,
            API_EMAIL: self.email,
            API_NAME: self.name,
            API_DASHBOARDS: [x.id for x in self.dashboards],
            API_FUNDS: [x.id for x in self.funds],
            API_CREATED_AT: self.created_at.isoformat(),
            API_UPDATED_AT: self.updated_at.isoformat()
        }
        return result

class Dashboard(db.Model):
    __tablename__ = 'dashboard'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = db.Column(db.UnicodeText)
    tasks = db.relationship('Task', lazy=True, backref='dashboard')
    users = db.relationship('UserAccount', back_populates='dashboard')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, name):
        self.name = name
    
    def dict(self):
        taskDetails = []
        for task in self.tasks:
            taskDetails.append(task.dict())
        
        result = {
            API_DASHBOARD_ID: str(self.id),
            API_NAME: self.name,
            API_CREATED_AT: self.created_at.isoformat(),
            API_UPDATED_AT: self.updated_at.isoformat(),
            API_TASKS: taskDetails,
        }
        return result
    
    def compactDict(self):
        result = {
            API_DASHBOARD_ID: str(self.id),
            API_NAME: self.name,
            API_CREATED_AT: self.created_at.isoformat(),
            API_UPDATED_AT: self.updated_at.isoformat(),
            API_TASKS: [x.id for x in self.tasks],
        }
        return result

class Task(db.Model):
    __tablename__ = 'task'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    parent_id = db.Column(UUID(as_uuid=True), db.ForeignKey('task.id'), nullable=True)
    children = db.relationship('Task',
                backref=db.backref('parent', remote_side=[id]))
    status = db.Column(db.Integer, default = 0)
    notification_level = db.Column(db.Integer, default = 0)
    priority = db.Column(db.Integer, default = 0)
    name = db.Column(db.UnicodeText)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    labels = db.Column(db.String, nullable=True)
    dashboard_id = db.Column(UUID(as_uuid=True), db.ForeignKey('dashboard.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

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
            API_START_TIME: self.start_time.isoformat() if self.start_time is not None else None,
            API_END_TIME: self.end_time.isoformat() if self.start_time is not None else None,
            API_LABELS: self.labels,
            API_CREATED_AT: self.created_at.isoformat(),
            API_UPDATED_AT: self.updated_at.isoformat()
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
    transactions = db.relationship('Transaction', backref='fund', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

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
        transactionDetails = []

        for exp in self.transactions:
            transactionDetails.append(exp.dict())

        result = {
            API_FUND_ID: str(self.id),
            API_NAME: self.name,
            API_START_TIME: self.start_time.isoformat() if self.start_time is not None else None,
            API_END_TIME: self.end_time.isoformat() if self.start_time is not None else None,
            API_BALANCE: self.balance,
            API_THRESHOLD: self.threshold,
            API_TRANSACTIONS: transactionDetails,
            API_CREATED_AT: self.created_at.isoformat(),
            API_UPDATED_AT: self.updated_at.isoformat()
        }

        return result
    
    def compactDict(self):
        result = {
            API_FUND_ID: str(self.id),
            API_NAME: self.name,
            API_START_TIME: self.start_time.isoformat() if self.start_time is not None else None,
            API_END_TIME: self.end_time.isoformat() if self.start_time is not None else None,
            API_BALANCE: self.balance,
            API_THRESHOLD: self.threshold,
            API_TRANSACTIONS: [x.id for x in self.transactions],
            API_CREATED_AT: self.created_at.isoformat(),
            API_UPDATED_AT: self.updated_at.isoformat()
        }
        return result

class Transaction(db.Model):
    __tablename__ = 'transaction'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    fund_id = db.Column(UUID(as_uuid=True), db.ForeignKey('fund.id'), nullable=False)
    purposes = db.Column(db.UnicodeText, nullable=True)
    time = db.Column(db.DateTime, nullable=True)
    spending = db.Column(db.BigInteger, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, fund_id, spending, purposes=None, time=None):
        self.fund_id = fund_id
        self.spending = spending
        if purposes is not None:
            self.purposes = purposes
        if time is not None:
            self.time = time
    
    def dict(self):
        result = {
            API_TRANSACTION_ID: str(self.id),
            API_FUND_ID: str(self.fund_id),
            API_PURPOSES: self.purposes,
            API_TIME: self.time,
            API_SPENDING: self.spending,
            API_CREATED_AT: self.created_at.isoformat(),
            API_UPDATED_AT: self.updated_at.isoformat()
        }
        return result

try:
    db.create_all()
    db.session.commit()
except Exception as e:
    print(str(e))
    sys.stdout.flush()
    db.session.rollback()