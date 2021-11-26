from flask import request, jsonify
from ..utils.definitions import *
from ..utils.cipher import *
from ..loader import *

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



def authorized(uid):
    return jsonify(message='AUTHORIZED'), 200