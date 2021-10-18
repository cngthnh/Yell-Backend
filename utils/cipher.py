import os

from jose import jwt
from jose import jwe
from jose import jwk
from jose.utils import base64url_decode
from jose.constants import ALGORITHMS
from database.models import UserAccount
from database.utils import db
from utils.definitions import *
from datetime import datetime, timedelta

def loadKeys():
    try:
        os.environ['YELL_ENC_KEY'] = open('enc','r').readline().strip()
        os.remove('enc')
        os.environ['YELL_SIG_KEY'] = open('sig','r').readline().strip()
        os.remove('sig')
    except Exception:
        pass

def encode(_dict, expired = DEFAULT_EXPIRATION_TIME):
    """ 
    Sign the dictionary
    Input: dictionary
    Output: JWT (text)
    """
    time_now = datetime.now()
    _dict[ISSUER_KEY] = YELL_ISSUER
    _dict[ISSUED_AT_KEY] = int(time_now.timestamp())
    _dict[NOT_BEFORE_KEY] = _dict[ISSUED_AT_KEY]
    _dict[EXPIRATION_KEY] = int((time_now + timedelta(minutes = expired)).timestamp())
    return jwt.encode(_dict, os.environ.get('YELL_SIG_KEY', None), algorithm=ALGORITHMS.HS256)

def verify(token):
    """
    Verify if the token was signed by the right key
    Input: JWT (text)
    Output: boolean
    """
    key = jwk.construct(os.environ.get('YELL_SIG_KEY', None), algorithm=ALGORITHMS.HS256)
    message, encoded_sig = token.rsplit(b'.', 1)
    decoded_sig = base64url_decode(encoded_sig)
    return key.verify(message, decoded_sig)

def decode(token):
    """ 
    Input: JWT (text)
    Output: dictionary
    """
    return jwt.decode(token, os.environ.get('YELL_SIG_KEY', None))

def encrypt(token):
    """
    Encrypt the signed token
    Input: JWT (text)
    Output: Encrypted JWT (JWE) (text)
    """
    return jwe.encrypt(token, os.environ.get('YELL_ENC_KEY', None), algorithm=ALGORITHMS.DIR, encryption=ALGORITHMS.A256GCM)

def decrypt(encrypted):
    """
    Decrypt to get the signed token
    Input: Encrypted JWT (JWE) (text)
    Output: JWT (text)
    """
    return jwe.decrypt(encrypted, os.environ.get('YELL_ENC_KEY', None))

def generateToken(_dict, expired = DEFAULT_EXPIRATION_TIME):
    """
    Sign and encrypt the dict
    Input: dictionary
    Output: JWE (text)
    """
    return encrypt(encode(_dict, expired=expired))

def parseToken(token):
    """
    Check if the token is signed and have correct credentials
    Input: JWE (text)
    Output: boolean
    """
    try:
        signedToken = decrypt(token)
        if not verify(signedToken):
            return False

        tokenDict = decode(signedToken)
        if tokenDict[ISSUER_KEY] != YELL_ISSUER:
            return None

    except Exception:
        return None

    return tokenDict