from flask import request

from core.views.auth_view import genTokenPair
from ..utils.cipher import *
from ..loader import *
from ..models.utils import *
from ..views.message_view import getMessage
import re

from functools import wraps
def tokenRequired(func):
    @wraps(func)
    def tokenCheck(*args, **kwargs):
        try:
            token = request.headers['Authorization']
            schema, token = token.split(maxsplit=1)
            if schema!='Bearer':
                return getMessage(INVALID_TOKEN_MESSAGE), 403
        except Exception:
            return getMessage(INVALID_TOKEN_MESSAGE), 403

        # parse token => dict of info
        try:
            tokenDict = decode(token)
            if tokenDict[ISSUER_KEY] != YELL_ISSUER:
                return getMessage(INVALID_TOKEN_MESSAGE), 403
            if (tokenDict[API_TOKEN_TYPE]!=ACCESS_TOKEN_TYPE):
                return getMessage(ACCESS_TOKEN_REQUIRED_MESSAGE), 403

            session = db.session.query(Session).filter_by(id=tokenDict[SESSION_ID_KEY]).first()

            if session is None:
                return getMessage(INVALID_SESSION_MESSAGE), 403

            if (int(session.updated_at.timestamp())!=tokenDict[ISSUED_AT_KEY]):
                try:
                    db.session.delete(session)
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                return getMessage(INVALID_SESSION_MESSAGE), 403

        except jwt.ExpiredSignatureError:
            return getMessage(EXPIRED_TOKEN_MESSAGE), 401
        except Exception:
            return getMessage(INVALID_TOKEN_MESSAGE), 403
        
        return func(*args, **kwargs, uid=session.user_id)
    return tokenCheck

def logout():
    try:
        token = request.headers['Authorization']
    except Exception:
        return getMessage(INVALID_TOKEN_MESSAGE), 403

    schema, token = token.split(maxsplit=1)
    if schema!='Bearer':
        return getMessage(INVALID_TOKEN_MESSAGE), 403

    # parse token => dict of info
    try:
        tokenDict = decode(token)
        if tokenDict[ISSUER_KEY] != YELL_ISSUER:
            return getMessage(INVALID_TOKEN_MESSAGE), 403
        if (tokenDict[API_TOKEN_TYPE]!=ACCESS_TOKEN_TYPE):
            return getMessage(ACCESS_TOKEN_REQUIRED_MESSAGE), 403

        session = db.session.query(Session).filter_by(id=tokenDict[SESSION_ID_KEY]).first()

        if session is None:
            return getMessage(INVALID_SESSION_MESSAGE), 403
            
        try:
            db.session.delete(session)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return getMessage(INVALID_SESSION_MESSAGE), 403

    except jwt.ExpiredSignatureError:
        return getMessage(EXPIRED_TOKEN_MESSAGE), 401
    except Exception:
        return getMessage(INVALID_TOKEN_MESSAGE), 403
    
    return getMessage(SUCCEED_MESSAGE), 200

def getToken():
    try:
        data = request.get_json()
        _uid = str(data[API_UID])
        _hash = str(data[API_HASH]).lower()
    except Exception as e:
        print(e)
        print(data)
        sys.stdout.flush()
        return getMessage(INVALID_CREDENTIALS_MESSAGE), 401

    if (not re.fullmatch(REGEX_UID, _uid)):
        return getMessage(INVALID_UID_MESSAGE), 400
    if (not re.fullmatch(REGEX_HASH, _hash)):
        return getMessage(INVALID_HASH_MESSAGE), 400

    try:
        if checkAccount(_uid, _hash):
            session = Session(_uid)

            try:
                db.session.add(session)
                db.session.commit()
            except Exception:
                db.session.rollback()
                return getMessage(INVALID_SESSION_MESSAGE), 403

            return genTokenPair(session), 200

        return getMessage(INACTIVATED_ACCOUNT_MESSAGE), 401
    except Exception as e:
        print(e)
        sys.stdout.flush()
        return getMessage(INVALID_CREDENTIALS_MESSAGE), 401

def refreshToken():
    try:
        token = request.headers['Authorization']
    except Exception:
        return getMessage(INVALID_TOKEN_MESSAGE), 403

    schema, token = token.split(maxsplit=1)
    if schema!='Bearer':
        return getMessage(INVALID_TOKEN_MESSAGE), 403

    # parse token => dict of info
    try:
        tokenDict = decode(token)
        if tokenDict[ISSUER_KEY] != YELL_ISSUER:
            return getMessage(INVALID_TOKEN_MESSAGE), 403
        if (tokenDict[API_TOKEN_TYPE]!=REFRESH_TOKEN_TYPE):
            return getMessage(REFRESH_TOKEN_REQUIRED_MESSAGE), 403

        print(tokenDict)
        sys.stdout.flush()
        
        session = db.session.query(Session).filter_by(id=tokenDict[SESSION_ID_KEY]).first()
        if (session is None):
            return getMessage(INVALID_SESSION_MESSAGE), 403
        
        if (int(session.updated_at.timestamp())!=tokenDict[ISSUED_AT_KEY]):
            try:
                db.session.delete(session)
                db.session.commit()
            except Exception:
                db.session.rollback()
            return getMessage(INVALID_SESSION_MESSAGE), 403

        iat = datetime.utcnow()
        session.updated_at = iat

        try:
            db.session.add(session)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return getMessage(INVALID_SESSION_MESSAGE), 403

        return genTokenPair(session), 200

    except jwt.ExpiredSignatureError:
        tokenDict = decode(token, options={'verify_exp': False})

        if tokenDict[ISSUER_KEY] != YELL_ISSUER:
            return getMessage(INVALID_TOKEN_MESSAGE), 403
        if (tokenDict[API_TOKEN_TYPE]!=REFRESH_TOKEN_TYPE):
            return getMessage(REFRESH_TOKEN_REQUIRED_MESSAGE), 403

        session = db.session.query(Session).filter_by(id=tokenDict[SESSION_ID_KEY]).first()
        if (session is not None):
            try:
                db.session.delete(session)
                db.session.commit()
            except Exception:
                db.session.rollback()
        return getMessage(EXPIRED_TOKEN_MESSAGE), 401
    except Exception:
        return getMessage(INVALID_TOKEN_MESSAGE), 403