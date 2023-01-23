from .models import *

def checkAccount(uid, hash):
    result = db.session.query(UserAccount).filter_by(id = uid, hash = hash).first()
    if (result is None):
        raise ValueError(INVALID_CREDENTIALS_MESSAGE)
    if (result.confirmed == False):
        return False
    return True

def cleanupConnection(session):
    session.close()
    db.get_engine(app).dispose()

def changeAccountStatus(uid, email, codeRecord = None):
    account = db.session.query(UserAccount).filter_by(id = uid, email = email).first()
    if account.confirmed:
        return None
    account.confirmed = True
    if (codeRecord is None):
        codeRecord = db.session.query(VerificationCode).filter_by(user_id = uid).first()
    
    try:
        db.session.add(account)
        db.session.delete(codeRecord)
        db.session.commit()
        return True
    except SQLAlchemyError:
        db.session.rollback()
        return False