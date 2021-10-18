from flask_sqlalchemy import SQLAlchemy
from database.utils import db

class UserAccount(db.Model):
    __tablename__ = 'user_account'
    id = db.Column(db.String(20), primary_key=True)
    email = db.Column(db.Text, unique=True)
    name = db.Column(db.UnicodeText)
    hash = db.Column(db.String(64))
    confirmed = db.Column(db.Boolean)
    def __init__(self, id, email, name, hash):
        self.id = id
        self.email = email
        self.name = name
        self.hash = hash
        self.confirmed = False

def checkAccount(uid, hash):
    if (db.session.query(UserAccount.uid).filter_by(id = uid, hash = hash).first() is None):
        return False
    return True