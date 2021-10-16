import os

from jose import jwt
from jose import jwe
from jose import jwk
from jose.utils import base64url_decode

from jose.constants import ALGORITHMS

YELL_ISSUER = 'Yell App by Yellion'

def loadKeys():
    try:
        os.environ['YELL_ENC_KEY'] = open('enc','r').readline().strip()
        os.remove('enc')
        os.environ['YELL_SIG_KEY'] = open('sig','r').readline().strip()
        os.remove('sig')
    except Exception:
        pass

def encode(_dict):
    """ 
    Sign the dictionary
    Input: dictionary
    Output: JWT (text)
    """
    _dict['iss'] = YELL_ISSUER
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

def generateToken(_dict):
    """
    Sign and encrypt the dict
    Input: dictionary
    Output: JWE (text)
    """
    return encrypt(encode(_dict))

def accountCheck(token):
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
        if tokenDict['iss'] != YELL_ISSUER:
            return False
        # account check in DB
    except Exception:
        return False

    return True