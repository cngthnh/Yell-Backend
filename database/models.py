from sqlalchemy.exc import SQLAlchemyError
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