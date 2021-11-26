from flask import request, jsonify
from ..loader import *
from ..models.models import UserAccount
from ..utils.cipher import *
from ..utils.email import *
from ..models.utils import *
from auth_controller import tokenRequired
import re

def verifyAccount(token):
    if not verifyToken(token):
        return jsonify(message=INVALID_TOKEN_MESSAGE), 403

    try:
        tokenDict = decode(token)
    except jwt.ExpiredSignatureError:
        return jsonify(message=EXPIRED_TOKEN_MESSAGE), 401

    try:
        result = changeAccountStatus(tokenDict[API_UID], tokenDict[API_EMAIL])
    except Exception:
        return jsonify(message=INVALID_TOKEN_MESSAGE), 403
    if result == True:
        return jsonify(message=VERIFIED_MESSAGE), 200
    else:
        return jsonify(message=INVALID_TOKEN_MESSAGE), 403

def createAccount():
    try:
        data = request.get_json()
        _uid = str(data[API_UID])
        _email = str(data[API_EMAIL])
        _hash = str(data[API_HASH]).lower()
        _name = str(data[API_NAME])
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    if (not re.fullmatch(REGEX_UID, _uid)):
        return jsonify(message=INVALID_UID_MESSAGE), 400
    if (not re.fullmatch(REGEX_EMAIL, _email)):
        return jsonify(message=INVALID_EMAIL_MESSAGE), 400
    if (not re.fullmatch(REGEX_HASH, _hash)):
        return jsonify(message=INVALID_HASH_MESSAGE), 400

    user = UserAccount(_uid, _email, _name, _hash)
    db.session.add(user)

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        print(str(e))
        sys.stdout.flush()
        return jsonify(message=FAILED_MESSAGE), 400

    sendVerificationEmail(_email, encode({API_UID: _uid, API_EMAIL: _email}, EMAIL_VERIFICATION_TIME), _name)

    return jsonify(message=PENDING_VERIFICATION_MESSAGE), 200

@tokenRequired
def updateAccount(uid):
    try:
        data = request.get_json()
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    fields = data.keys()
    
    if (not re.fullmatch(REGEX_UID, uid)):
            return jsonify(message=INVALID_UID_MESSAGE), 400
    user = db.session.query(UserAccount).filter_by(id=uid).first()
    if (user is None):
        return jsonify(message=USER_DOES_NOT_EXISTS_MESSAGE), 404

    emailChanged = False
    try:
        if (API_EMAIL in fields and data[API_EMAIL] is not None):
            user.email = str(data[API_EMAIL])
            if (not re.fullmatch(REGEX_EMAIL, user.email)):
                return jsonify(message=INVALID_EMAIL_MESSAGE), 400
            user.confirmed = False
            emailChanged = True
        if (API_NAME in fields and data[API_NAME] is not None):
            user.name = str(data[API_NAME])
        if (API_HASH in fields and data[API_HASH] is not None):
            user.hash = str(data[API_HASH])
            if (not re.fullmatch(REGEX_HASH, user.hash)):
                return jsonify(message=INVALID_HASH_MESSAGE), 400
    except Exception:
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    try:
        user.updated_at = datetime.utcnow()
        db.session.add(user)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        print(str(e))
        sys.stdout.flush()
        return jsonify(message=FAILED_MESSAGE), 400

    if emailChanged:
        sendVerificationEmail(user.email, encode({API_UID: uid, API_EMAIL: user.email}, EMAIL_VERIFICATION_TIME), user.name)
        return jsonify(message=PENDING_VERIFICATION_MESSAGE), 200

    return jsonify(message=SUCCEED_MESSAGE), 200

@tokenRequired
def deleteAccount(uid):
    if (not re.fullmatch(REGEX_UID, uid)):
            return jsonify(message=INVALID_UID_MESSAGE), 400
    user = db.session.query(UserAccount).filter_by(id=uid).first()
    if (user is None):
        return jsonify(message=USER_DOES_NOT_EXISTS_MESSAGE), 404

    try:
        db.session.delete(user)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        print(str(e))
        sys.stdout.flush()
        return jsonify(message=FAILED_MESSAGE), 400

    return jsonify(message=SUCCEED_MESSAGE), 200

def checkAvailability():
    _email = request.args.get(API_EMAIL)
    _uid = request.args.get(API_UID)

    if (_email is None and _uid is None):
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    elif ((_email is not None) and (_uid is not None)):
        return jsonify(message=INVALID_DATA_MESSAGE), 400

    elif (_uid is None):
        if db.session.query(UserAccount.email).filter_by(email=_email).first() is None:
            return jsonify(message=OK_MESSAGE), 200
        return jsonify(message=INVALID_EMAIL_MESSAGE), 409
    
    else:
        if db.session.query(UserAccount.id).filter_by(id=_uid).first() is None:
            return jsonify(message=OK_MESSAGE), 200
        return jsonify(message=INVALID_UID_MESSAGE), 409

@tokenRequired
def getUserProfile(uid):

    user = db.session.query(UserAccount).filter_by(id=uid).first()

    if (user is not None):
        fetchType = request.args.get(API_FETCH)

        if (fetchType==API_FULL):
            return jsonify(user.dict()), 200
        elif (fetchType==API_COMPACT):
            return jsonify(user.compactDict()), 200
        else:
            return jsonify(user.compactDict()), 200

    return jsonify(USER_DOES_NOT_EXISTS_MESSAGE), 404