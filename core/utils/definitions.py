## Yell Consts ##
YELL_ISSUER = 'Yell App by Yellion'
EMAIL_VRF_TEMPLATE_HTML = 'email_verification_template.html'
EMAIL_VRF_TEMPLATE_TXT = 'email_verification_template.txt'
MAX_UID_LENGTH = 64

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
VERIFIED_MESSAGE = 'VERIFIED' # verified account
INACTIVATED_ACCOUNT_MESSAGE = 'INACTIVATED_ACCOUNT'
EXPIRED_TOKEN_MESSAGE = 'EXPIRED_TOKEN'
INVALID_DASHBOARD_MESSAGE = 'INVALID_DASHBOARD'
FORBIDDEN_MESSAGE = 'FORBIDDEN'
USER_DOES_NOT_EXISTS_MESSAGE = 'USER_DOES_NOT_EXISTS'

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
API_NAME = 'name'
API_STATUS = 'status'
API_PRIORITY = 'priority'
API_NOTI_LEVEL = 'noti_level'
API_PARENT_ID = 'parent_id'
API_START_TIME = 'start_time'
API_END_TIME = 'end_time'
API_LABELS = 'labels'
API_TASK_ID = 'task_id'
API_DASHBOARD_ID = 'dashboard_id'

# Endpoints
GET_USER_ENDPOINT = '/api/users/<user_id>' # GET
USERS_ENDPOINT = '/api/users' # POST, PATCH, DELETE
EMAIL_VRF_ENDPOINT = '/api/users/verify/<token>' # GET
EMAIL_VRF_SIGNATURE = '/api/users/verify/'
AUTH_ENDPOINT = '/api/users/auth' # POST
AUTHORIZED_TEST_ENDPOINT = '/api/users/authorized' 
USERS_CHECK_ENDPOINT = '/api/users/check' # GET
TASKS_ENDPOINT = '/api/tasks' # POST, PATCH, DELETE
GET_TASK_ENDPOINT = '/api/tasks/<task_id>' # GET
DASHBOARDS_ENDPOINT = '/api/dashboards' # POST, PATCH, DELETE
GET_DASHBOARD_ENDPOINT = '/api/dashboards/<dashboard_id>' # GET