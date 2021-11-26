from .models import *

def checkAccount(uid, hash):
    result = db.session.query(UserAccount).filter_by(id = uid, hash = hash).first()
    if (result is None):
        raise ValueError(INVALID_CREDENTIALS_MESSAGE)
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