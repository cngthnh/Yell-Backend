from flask import request, jsonify
from ..utils.cipher import *
from ..loader import *
from ..models.models import Session
from ..models.utils import *
import re

from functools import wraps
def tokenRequired(func):
    @wraps(func)
    def tokenCheck(*args, **kwargs):
        try:
            token = request.headers['Authorization']
            schema, token = token.split(maxsplit=1)
            if schema!='Bearer':
                return jsonify(message=INVALID_TOKEN_MESSAGE), 403
        except Exception:
            return jsonify(message=INVALID_TOKEN_MESSAGE), 403

        # parse token => dict of info
        try:
            tokenDict = decode(token)
            if tokenDict[ISSUER_KEY] != YELL_ISSUER:
                return jsonify(message=INVALID_TOKEN_MESSAGE), 403
            if (tokenDict[API_TOKEN_TYPE]!=ACCESS_TOKEN_TYPE):
                return jsonify(message=ACCESS_TOKEN_REQUIRED_MESSAGE), 403

            session = db.session.query(Session).filter_by(id=tokenDict[SESSION_ID_KEY]).first()

            if session is None:
                return jsonify(message=INVALID_SESSION_MESSAGE), 403

            if (int(session.updated_at.timestamp())!=tokenDict[ISSUED_AT_KEY]):
                try:
                    db.session.delete(session)
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                return jsonify(message=INVALID_SESSION_MESSAGE), 403

        except jwt.ExpiredSignatureError:
            return jsonify(message=EXPIRED_TOKEN_MESSAGE), 401
        except Exception:
            return jsonify(message=INVALID_TOKEN_MESSAGE), 403
        
        return func(*args, **kwargs, uid=session.user_id)
    return tokenCheck

def logout():
    try:
        token = request.headers['Authorization']
    except Exception:
        return jsonify(message=INVALID_TOKEN_MESSAGE), 403

    schema, token = token.split(maxsplit=1)
    if schema!='Bearer':
        return jsonify(message=INVALID_TOKEN_MESSAGE), 403

    # parse token => dict of info
    try:
        tokenDict = decode(token)
        if tokenDict[ISSUER_KEY] != YELL_ISSUER:
            return jsonify(message=INVALID_TOKEN_MESSAGE), 403
        if (tokenDict[API_TOKEN_TYPE]!=ACCESS_TOKEN_TYPE):
            return jsonify(message=ACCESS_TOKEN_REQUIRED_MESSAGE), 403

        session = db.session.query(Session).filter_by(id=tokenDict[SESSION_ID_KEY]).first()

        if session is None:
            return jsonify(message=INVALID_SESSION_MESSAGE), 403
            
        try:
            db.session.delete(session)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify(message=INVALID_SESSION_MESSAGE), 403

    except jwt.ExpiredSignatureError:
        return jsonify(message=EXPIRED_TOKEN_MESSAGE), 401
    except Exception:
        return jsonify(message=INVALID_TOKEN_MESSAGE), 403
    
    return jsonify(message=SUCCEED_MESSAGE), 200

def getToken():
    try:
        data = request.get_json()
        _uid = str(data[API_UID])
        _hash = str(data[API_HASH]).lower()
    except Exception as e:
        print(e)
        print(data)
        sys.stdout.flush()
        return jsonify(message=INVALID_CREDENTIALS_MESSAGE), 401

    if (not re.fullmatch(REGEX_UID, _uid)):
        return jsonify(message=INVALID_UID_MESSAGE), 400
    if (not re.fullmatch(REGEX_HASH, _hash)):
        return jsonify(message=INVALID_HASH_MESSAGE), 400

    try:
        if checkAccount(_uid, _hash):
            session = Session(_uid)

            try:
                db.session.add(session)
                db.session.commit()
            except Exception:
                db.session.rollback()
                return jsonify(message=INVALID_SESSION_MESSAGE), 403

            _accessTokenDict = {API_TOKEN_TYPE: ACCESS_TOKEN_TYPE, SESSION_ID_KEY: str(session.id)}
            _refreshTokenDict = {API_TOKEN_TYPE: REFRESH_TOKEN_TYPE, SESSION_ID_KEY: str(session.id)}

            return jsonify(
                        access_token=encode(_accessTokenDict, ACCESS_TOKEN_EXP_TIME, iat=session.updated_at),
                        refresh_token=encode(_refreshTokenDict, iat=session.updated_at)
                        ), 200
        return jsonify(message=INACTIVATED_ACCOUNT_MESSAGE), 401
    except Exception as e:
        print(e)
        sys.stdout.flush()
        return jsonify(message=INVALID_CREDENTIALS_MESSAGE), 401

def refreshToken():
    try:
        token = request.headers['Authorization']
    except Exception:
        return jsonify(message=INVALID_TOKEN_MESSAGE), 403

    schema, token = token.split(maxsplit=1)
    if schema!='Bearer':
        return jsonify(message=INVALID_TOKEN_MESSAGE), 403

    # parse token => dict of info
    try:
        tokenDict = decode(token)
        if tokenDict[ISSUER_KEY] != YELL_ISSUER:
            return jsonify(message=INVALID_TOKEN_MESSAGE), 403
        if (tokenDict[API_TOKEN_TYPE]!=REFRESH_TOKEN_TYPE):
            return jsonify(message=REFRESH_TOKEN_REQUIRED_MESSAGE), 403

        print(tokenDict)
        sys.stdout.flush()
        
        session = db.session.query(Session).filter_by(id=tokenDict[SESSION_ID_KEY]).first()
        if (session is None):
            return jsonify(message=INVALID_SESSION_MESSAGE), 403
        
        if (int(session.updated_at.timestamp())!=tokenDict[ISSUED_AT_KEY]):
            try:
                db.session.delete(session)
                db.session.commit()
            except Exception:
                db.session.rollback()
            return jsonify(message=INVALID_SESSION_MESSAGE), 403

        iat = datetime.utcnow()
        session.updated_at = iat

        try:
            db.session.add(session)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify(message=INVALID_SESSION_MESSAGE), 403

        _refreshTokenDict = {API_TOKEN_TYPE: REFRESH_TOKEN_TYPE, SESSION_ID_KEY: str(session.id)}
        _accessTokenDict = {API_TOKEN_TYPE: ACCESS_TOKEN_TYPE, SESSION_ID_KEY: str(session.id)}

        return jsonify(access_token=encode(_accessTokenDict, ACCESS_TOKEN_EXP_TIME, iat=iat), 
                        refresh_token=encode(_refreshTokenDict, iat=iat)), 200

    except jwt.ExpiredSignatureError:
        tokenDict = decode(token, options={'verify_exp': False})

        if tokenDict[ISSUER_KEY] != YELL_ISSUER:
            return jsonify(message=INVALID_TOKEN_MESSAGE), 403
        if (tokenDict[API_TOKEN_TYPE]!=REFRESH_TOKEN_TYPE):
            return jsonify(message=REFRESH_TOKEN_REQUIRED_MESSAGE), 403

        session = db.session.query(Session).filter_by(id=tokenDict[SESSION_ID_KEY]).first()
        if (session is not None):
            try:
                db.session.delete(session)
                db.session.commit()
            except Exception:
                db.session.rollback()
        return jsonify(message=EXPIRED_TOKEN_MESSAGE), 401
    except Exception:
        return jsonify(message=INVALID_TOKEN_MESSAGE), 403