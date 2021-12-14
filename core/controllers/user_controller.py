from flask import request, jsonify

from ..utils.utils import generateCode
from ..loader import *
from ..utils.cipher import *
from ..utils.email import *
from ..models.utils import *
from .auth_controller import tokenRequired
from ..views.message_view import getMessage
from ..views.user_view import genUserInfo
import re

def verifyAccount(token):
    if not verifyToken(token):
        return getMessage(message=INVALID_TOKEN_MESSAGE), 403

    try:
        tokenDict = decode(token)
    except jwt.ExpiredSignatureError:
        return getMessage(message=EXPIRED_TOKEN_MESSAGE), 401

    try:
        result = changeAccountStatus(tokenDict[API_UID], tokenDict[API_EMAIL])
    except Exception:
        return getMessage(message=INVALID_TOKEN_MESSAGE), 403
    
    if (result is None):
        return getMessage(message=INVALID_REQUEST_MESSAGE), 400

    if result == True:
        return getMessage(message=VERIFIED_MESSAGE), 200
    else:
        return getMessage(message=INVALID_TOKEN_MESSAGE), 403

def createAccount():
    try:
        data = request.get_json()
        _uid = str(data[API_UID])
        _email = str(data[API_EMAIL])
        _hash = str(data[API_HASH]).lower()
        _name = str(data[API_NAME])
    except Exception:
        return getMessage(message=INVALID_DATA_MESSAGE), 400

    if (not re.fullmatch(REGEX_UID, _uid)):
        return getMessage(message=INVALID_UID_MESSAGE), 400
    if (not re.fullmatch(REGEX_EMAIL, _email)):
        return getMessage(message=INVALID_EMAIL_MESSAGE), 400
    if (not re.fullmatch(REGEX_HASH, _hash)):
        return getMessage(message=INVALID_HASH_MESSAGE), 400

    user = UserAccount(_uid, _email, _name, _hash)

    veriRecord = db.session.query(VerificationCode).filter_by(user_id=_uid, code_type=CODE_TYPE_EMAIL).first()
    if (veriRecord is not None):
        veriRecord.refresh()
    else:
        veriRecord = VerificationCode(user.id, CODE_TYPE_EMAIL)

    try:
        db.session.add(user)
        db.session.add(veriRecord)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        print(str(e))
        sys.stdout.flush()
        return getMessage(message=FAILED_MESSAGE), 400

    sendVerificationEmail(_email, encode({API_UID: _uid, API_EMAIL: _email}, EMAIL_VERIFICATION_TIME), _name, veriRecord.code)

    return getMessage(message=PENDING_VERIFICATION_MESSAGE), 200

@tokenRequired
def updateAccount(uid):
    try:
        data = request.get_json()
    except Exception:
        return getMessage(message=INVALID_DATA_MESSAGE), 400

    fields = data.keys()
    
    if (not re.fullmatch(REGEX_UID, uid)):
            return getMessage(message=INVALID_UID_MESSAGE), 400
    user = db.session.query(UserAccount).filter_by(id=uid).first()
    if (user is None):
        return getMessage(message=USER_DOES_NOT_EXISTS_MESSAGE), 404

    emailChanged = False
    veriRecord = None
    try:
        if (API_EMAIL in fields and data[API_EMAIL] is not None):
            user.email = str(data[API_EMAIL])
            if (not re.fullmatch(REGEX_EMAIL, user.email)):
                return getMessage(message=INVALID_EMAIL_MESSAGE), 400
            user.confirmed = False
            emailChanged = True
            veriRecord = db.session.query(VerificationCode).filter_by(user_id=uid, code_type=CODE_TYPE_EMAIL).first()
            if (veriRecord is not None):
                veriRecord.refresh()
            else:
                veriRecord = VerificationCode(user.id, CODE_TYPE_EMAIL)

        if (API_NAME in fields and data[API_NAME] is not None):
            user.name = str(data[API_NAME])
        if (API_HASH in fields and data[API_HASH] is not None):
            user.hash = str(data[API_HASH])
            if (not re.fullmatch(REGEX_HASH, user.hash)):
                return getMessage(message=INVALID_HASH_MESSAGE), 400
    except Exception:
        return getMessage(message=INVALID_DATA_MESSAGE), 400

    try:
        user.updated_at = datetime.utcnow()
        db.session.add(user)
        if veriRecord is not None:
            db.session.add(veriRecord)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        print(str(e))
        sys.stdout.flush()
        return getMessage(message=FAILED_MESSAGE), 400

    if emailChanged:
        sendVerificationEmail(user.email, encode({API_UID: uid, API_EMAIL: user.email}, EMAIL_VERIFICATION_TIME), user.name, veriRecord.code)
        return getMessage(message=PENDING_VERIFICATION_MESSAGE), 200

    return getMessage(message=SUCCEED_MESSAGE), 200

@tokenRequired
def deleteAccount(uid):
    if (not re.fullmatch(REGEX_UID, uid)):
            return getMessage(message=INVALID_UID_MESSAGE), 400
    user = db.session.query(UserAccount).filter_by(id=uid).first()
    if (user is None):
        return getMessage(message=USER_DOES_NOT_EXISTS_MESSAGE), 404

    try:
        db.session.delete(user)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        print(str(e))
        sys.stdout.flush()
        return getMessage(message=FAILED_MESSAGE), 400

    return getMessage(message=SUCCEED_MESSAGE), 200

def checkAvailability():
    _email = request.args.get(API_EMAIL)
    _uid = request.args.get(API_UID)

    if (_email is None and _uid is None):
        return getMessage(message=INVALID_DATA_MESSAGE), 400

    elif ((_email is not None) and (_uid is not None)):
        return getMessage(message=INVALID_DATA_MESSAGE), 400

    elif (_uid is None):
        if db.session.query(UserAccount.email).filter_by(email=_email).first() is None:
            return getMessage(message=OK_MESSAGE), 200
        return getMessage(message=INVALID_EMAIL_MESSAGE), 409
    
    else:
        if db.session.query(UserAccount.id).filter_by(id=_uid).first() is None:
            return getMessage(message=OK_MESSAGE), 200
        return getMessage(message=INVALID_UID_MESSAGE), 409

@tokenRequired
def getUserProfile(uid):

    user = db.session.query(UserAccount).filter_by(id=uid).first()

    if (user is not None):
        fetchType = request.args.get(API_FETCH)

        if (fetchType==API_FULL):
            return genUserInfo(user.dict()), 200
        elif (fetchType==API_COMPACT):
            return genUserInfo(user.compactDict()), 200
        else:
            return genUserInfo(user.compactDict()), 200

    return getMessage(message=USER_DOES_NOT_EXISTS_MESSAGE), 404

def verifyAccountByCode():
    try:
        data = request.get_json()
    except Exception:
        return getMessage(message=INVALID_DATA_MESSAGE), 400

    try:
        _uid = str(data[API_UID])
        _code = str(data[API_CODE])
        _email = str(data[API_EMAIL])
    except Exception:
        return getMessage(message=INVALID_DATA_MESSAGE), 400

    if (not re.fullmatch(REGEX_UID, _uid)):
        return getMessage(message=INVALID_UID_MESSAGE), 400

    veriRecord = db.session.query(VerificationCode).filter_by(user_id=_uid, code_type=CODE_TYPE_EMAIL).first()
    if (veriRecord is None):
        return getMessage(message=INVALID_REQUEST_MESSAGE), 400

    if (_code == veriRecord.code):
        result = changeAccountStatus(_uid, _email, veriRecord)
        if (result is None):
            return getMessage(message=INVALID_REQUEST_MESSAGE), 400
        if (result == True):
            return getMessage(message=SUCCEED_MESSAGE), 200
        return getMessage(message=FAILED_MESSAGE), 400
    
    return getMessage(message=INVALID_REQUEST_MESSAGE), 400

def resendVerificationEmail():
    try:
        data = request.get_json()
    except Exception:
        return getMessage(message=INVALID_DATA_MESSAGE), 400

    try:
        _uid = str(data[API_UID])
    except Exception:
        return getMessage(message=INVALID_DATA_MESSAGE), 400

    if (not re.fullmatch(REGEX_UID, _uid)):
        return getMessage(message=INVALID_UID_MESSAGE), 400

    user = db.session.query(UserAccount).filter_by(id=_uid).first()
    if (user is None):
        return getMessage(message=USER_DOES_NOT_EXISTS_MESSAGE), 404
    
    if (user.confirmed):
        return getMessage(message=INVALID_REQUEST_MESSAGE), 400

    veriRecord = db.session.query(VerificationCode).filter_by(user_id=_uid, code_type=CODE_TYPE_EMAIL).first()
    if (veriRecord is None):
        return getMessage(message=INVALID_REQUEST_MESSAGE), 400
    
    try:
        veriRecord.refresh()
        db.session.add(veriRecord)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        print(str(e))
        sys.stdout.flush()
        return getMessage(message=FAILED_MESSAGE), 400

    sendVerificationEmail(user.email, encode({API_UID: _uid, API_EMAIL: user.email}, EMAIL_VERIFICATION_TIME), user.name, veriRecord.code)
    return getMessage(message=PENDING_VERIFICATION_MESSAGE), 200