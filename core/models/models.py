from sqlalchemy.exc import SQLAlchemyError
import sys

from ..utils.utils import generateCode
from ..utils.definitions import *
from ..loader import db
import uuid
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from ..utils.s3 import S3Handler

class DashboardPermission(db.Model):
    __tablename__ = 'dashboard_permission'
    user_id = db.Column(db.String(MAX_UID_LENGTH), db.ForeignKey('user_account.id'), primary_key=True)
    dashboard_id = db.Column(UUID(as_uuid=True), db.ForeignKey('dashboard.id'), primary_key=True)
    role = db.Column(db.String)
    dashboard = db.relationship('Dashboard', back_populates='users')
    user = db.relationship('UserAccount', back_populates='dashboards')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    dashboards = db.relationship('DashboardPermission', back_populates='user', cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='owner', lazy=True, cascade='all, delete-orphan')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    sessions = db.relationship('Session', backref='user', lazy=True, cascade='all, delete-orphan')

    def __init__(self, id, email, name, hash):
        self.id = id
        self.email = email
        self.name = name
        self.hash = hash
        self.confirmed = False
    
    def dict(self):
        dashboardDetails = []
        budgetDetails = []

        for dashboard in self.dashboards:
            dashboardDetails.append(dashboard.dict())

        for budget in self.budgets:
            budgetDetails.append(budget.dict())

        result = {
            API_UID: self.id,
            API_EMAIL: self.email,
            API_NAME: self.name,
            API_DASHBOARDS: dashboardDetails,
            API_BUDGETS: budgetDetails,
            API_CREATED_AT: self.created_at.isoformat(),
            API_UPDATED_AT: self.updated_at.isoformat()
        }
        return result
    
    def compactDict(self):
        result = {
            API_UID: self.id,
            API_EMAIL: self.email,
            API_NAME: self.name,
            API_DASHBOARDS: [x.dashboard_id for x in self.dashboards],
            API_BUDGETS: [x.id for x in self.budgets],
            API_CREATED_AT: self.created_at.isoformat(),
            API_UPDATED_AT: self.updated_at.isoformat()
        }
        return result

class Session(db.Model):
    __tablename__ = 'session'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = db.Column(db.String(MAX_UID_LENGTH), db.ForeignKey('user_account.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, user_id):
        self.user_id = user_id

class Dashboard(db.Model):
    __tablename__ = 'dashboard'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = db.Column(db.UnicodeText)
    tasks = db.relationship('Task', lazy=True, backref='dashboard', cascade='all, delete-orphan')
    users = db.relationship('DashboardPermission', back_populates='dashboard', cascade='all, delete-orphan')
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
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    parent_id = db.Column(UUID(as_uuid=True), db.ForeignKey('task.id'), nullable=True)
    children = db.relationship('Task',
                backref=db.backref('parent', remote_side=[id]))
    status = db.Column(db.Integer, default = 0)
    notification_level = db.Column(db.Integer, default = 0)
    priority = db.Column(db.Integer, default = 0)
    name = db.Column(db.UnicodeText)
    content = db.Column(db.UnicodeText, nullable=True)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    labels = db.Column(db.String, nullable=True)
    files = db.Column(db.String, nullable=True)
    dashboard_id = db.Column(UUID(as_uuid=True), db.ForeignKey('dashboard.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, name, dashboard_id, content=None, status = None, notification_level = None, priority = None, parent_id=None, start_time=None, end_time=None, labels=None):
        self.name = name
        self.dashboard_id = dashboard_id
        if status is not None:
            self.status = int(status)
        if content is not None:
            self.content = content
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
        
        s3 = S3Handler()

        files = []
        thisId = str(self.id)
        if self.files is not None:
            for file in self.files.split(','):
                files.append({API_FILE_NAME: file, API_URL: s3.getLink(thisId, file)})

        result = {
            API_NAME: self.name,
            API_CONTENT: self.content,
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
            API_UPDATED_AT: self.updated_at.isoformat(),
            API_FILES: files
        }
        return result


class Budget(db.Model):
    __tablename__ = 'budget'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    owner_id = db.Column(db.String(MAX_UID_LENGTH), db.ForeignKey('user_account.id'), nullable=False)
    name = db.Column(db.UnicodeText, nullable=False)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    balance = db.Column(db.BigInteger, nullable=False)
    threshold = db.Column(db.BigInteger, nullable=True)
    transactions = db.relationship('Transaction', backref='budget', lazy=True, cascade='all, delete-orphan')
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
            API_BUDGET_ID: str(self.id),
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
            API_BUDGET_ID: str(self.id),
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
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    budget_id = db.Column(UUID(as_uuid=True), db.ForeignKey('budget.id'), nullable=False)
    purposes = db.Column(db.UnicodeText, nullable=True)
    time = db.Column(db.DateTime, nullable=True)
    amount = db.Column(db.BigInteger, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, budget_id, amount, purposes=None, time=None):
        self.budget_id = budget_id
        self.amount = amount
        if purposes is not None:
            self.purposes = purposes
        if time is not None:
            self.time = time
    
    def dict(self):
        result = {
            API_TRANSACTION_ID: str(self.id),
            API_BUDGET_ID: str(self.budget_id),
            API_PURPOSES: self.purposes,
            API_TIME: self.time,
            API_AMOUNT: self.amount,
            API_CREATED_AT: self.created_at.isoformat(),
            API_UPDATED_AT: self.updated_at.isoformat()
        }
        return result

class VerificationCode(db.Model):
    __tablename__ = 'verification_code'
    user_id = db.Column(db.String(MAX_UID_LENGTH), primary_key=True, nullable=False)
    code_type = db.Column(db.Integer, primary_key=True, nullable=False)
    code = db.Column(db.String(4), nullable=False, default=generateCode)
    tries = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, user_id, code_type):
        self.user_id = user_id
        self.code_type = code_type
    
    def refresh(self):
        self.code = generateCode()
        self.updated_at = datetime.utcnow()

try:
    db.create_all()
    db.session.commit()
except Exception as e:
    print(str(e))
    sys.stdout.flush()
    db.session.rollback()