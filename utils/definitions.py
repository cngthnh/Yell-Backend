## Yell Consts ##
YELL_ISSUER = 'Yell App by Yellion'

## Messages ##
INVALID_TOKEN_MESSAGE = 'INVALID_TOKEN' # None / can't be decrypt / fault signature tokens
INVALID_CREDENTIALS_MESSAGE = 'INVALID_CREDENTIALS' # None / invalid uid or hash
INVALID_DATA_MESSAGE = 'INVALID_DATA' # general use
OK_MESSAGE = 'OK' #general use
FAILED_MESSAGE = 'FAILED' # general use
INVALID_EMAIL_MESSAGE = 'INVALID_EMAIL' # email addresses with undefined format or being used by another account
INVALID_UID_MESSAGE = 'INVALID_UID' # uid contains unaccepted chars or used by another account
SUCCEED_MESSAGE = 'SUCCEED' # something done successfully
FAILED_MESSAGE = 'FAILED' # something went wrong
PENDING_VERIFICATION_MESSAGE = 'PENDING_VERIFICATION' # account needs to be verified by email
EMAIL_VERIFICATION_TIME = 10 # 10 minutes
DEFAULT_EXPIRATION_TIME = 43800 # 1 month

## Key names ##
ISSUER_KEY = 'iss'
ISSUED_AT_KEY = 'iat'
EXPIRATION_KEY = 'exp'
NOT_BEFORE_KEY = 'nbf'

## Definitions for API key names ##
API_TOKEN = 'token'
API_UID = 'uid'
API_HASH = 'hash'
API_EMAIL = 'email'
API_USER_FULL_NAME = 'name'