from core.views.message_view import getMessage
from ..models.models import Session
from .json_view import makeJson
from ..utils.cipher import *
from ..utils.definitions import *

def genTokenPair(session: Session) -> str:

    _accessTokenDict = {API_TOKEN_TYPE: ACCESS_TOKEN_TYPE, SESSION_ID_KEY: str(session.id)}
    _refreshTokenDict = {API_TOKEN_TYPE: REFRESH_TOKEN_TYPE, SESSION_ID_KEY: str(session.id)}
    
    return getMessage(access_token=encode(_accessTokenDict, ACCESS_TOKEN_EXP_TIME, iat=session.updated_at),
                        refresh_token=encode(_refreshTokenDict, iat=session.updated_at))