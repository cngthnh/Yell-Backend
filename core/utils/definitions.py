## Yell Consts ##
YELL_ISSUER = 'Yell App by Yellion'
EMAIL_VRF_TEMPLATE_HTML = 'email_verification_template.html'
EMAIL_VRF_TEMPLATE_TXT = 'email_verification_template.txt'
DASHBOARD_INV_TEMPLATE_TXT = 'dashboard_invitation_template.txt'
MAX_UID_LENGTH = 64
VIEWER_ROLE = 'viewer'
EDITOR_ROLE = 'editor'
ADMIN_ROLE = 'admin'
DASHBOARD_ROLES = [VIEWER_ROLE, EDITOR_ROLE, ADMIN_ROLE]
VIEW_PERMISSION = 'view'
EDIT_PERMISSION = 'edit'
INVITE_PERMISSION = 'invite'
DELETE_PERMISSION = 'delete'

DASHBOARD_PERMISSION = {
    VIEWER_ROLE: [VIEW_PERMISSION],
    EDITOR_ROLE: [VIEW_PERMISSION, EDIT_PERMISSION],
    ADMIN_ROLE: [VIEW_PERMISSION, EDIT_PERMISSION, INVITE_PERMISSION, DELETE_PERMISSION]
}

ACCESS_TOKEN_TYPE = 'access'
REFRESH_TOKEN_TYPE = 'refresh'

## Messages ##
INVALID_TOKEN_MESSAGE = 'INVALID_TOKEN' # None / can't be decrypt / fault signature tokens
INVALID_CREDENTIALS_MESSAGE = 'INVALID_CREDENTIALS' # None / invalid uid or hash
INVALID_DATA_MESSAGE = 'INVALID_DATA' # general use
INVALID_NAME_MESSAGE = 'INVALID_NAME'
INVALID_HASH_MESSAGE = 'INVALID_HASH'
OK_MESSAGE = 'OK' #general use
FAILED_MESSAGE = 'FAILED' # general use
INVALID_EMAIL_MESSAGE = 'INVALID_EMAIL' # email addresses with undefined format or being used by another account
INVALID_UID_MESSAGE = 'INVALID_UID' # uid contains unaccepted chars or used by another account
SUCCEED_MESSAGE = 'SUCCEED' # something done successfully
FAILED_MESSAGE = 'FAILED' # something went wrong
PENDING_VERIFICATION_MESSAGE = 'PENDING_VERIFICATION' # account needs to be verified by email
EMAIL_VERIFICATION_TIME = 10 # 10 minutes
ACCESS_TOKEN_EXP_TIME = 30 # 30 minutes
DEFAULT_EXPIRATION_TIME = 43800 # 1 month
VERIFIED_MESSAGE = 'VERIFIED' # verified account
INACTIVATED_ACCOUNT_MESSAGE = 'INACTIVATED_ACCOUNT'
EXPIRED_TOKEN_MESSAGE = 'EXPIRED_TOKEN'
INVALID_DASHBOARD_MESSAGE = 'INVALID_DASHBOARD'
FORBIDDEN_MESSAGE = 'FORBIDDEN'
USER_DOES_NOT_EXISTS_MESSAGE = 'USER_DOES_NOT_EXISTS'
DASHBOARD_DOES_NOT_EXISTS_MESSAGE = 'DASHBOARD_DOES_NOT_EXISTS'
TASK_DOES_NOT_EXISTS_MESSAGE = 'TASK_DOES_NOT_EXISTS'
BUDGET_DOES_NOT_EXISTS_MESSAGE = 'BUDGET_DOES_NOT_EXISTS'
TRANSACTION_DOES_NOT_EXISTS_MESSAGE = 'TRANSACTION_DOES_NOT_EXISTS'
INVITATION_SENT_MESSAGE = 'INVITATION_SENT'
ACCESS_TOKEN_REQUIRED_MESSAGE = 'ACCESS_TOKEN_REQUIRED'
REFRESH_TOKEN_REQUIRED_MESSAGE = 'REFRESH_TOKEN_REQUIRED'
INVALID_SESSION_MESSAGE = 'INVALID_SESSION'
INVALID_REQUEST_MESSAGE = 'INVALID_REQUEST'

## Key names ##
ISSUER_KEY = 'iss'
ISSUED_AT_KEY = 'iat'
EXPIRATION_KEY = 'exp'
SESSION_ID_KEY = 'session_id'
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
API_DASHBOARDS = 'dashboards'
API_BUDGETS = 'budgets'
API_BUDGET_ID = 'budget_id'
API_SUBTASKS = 'subtasks'
API_TASKS = 'tasks'
API_BALANCE = 'balance'
API_THRESHOLD = 'threshold'
API_TRANSACTIONS = 'transactions'
API_TRANSACTION_ID = 'transaction_id'
API_PURPOSES = 'purposes'
API_TIME = 'time'
API_AMOUNT = 'amount'
API_FETCH = 'fetch'
API_FULL = 'full'
API_COMPACT = 'compact'
API_CREATED_AT = 'created_at'
API_UPDATED_AT = 'updated_at'
API_INVITED_BY = 'invited_by'
API_ROLE = 'role'
API_CONTENT = 'content'
API_TOKEN_TYPE = 'token_type'
API_CODE = 'code'

# Endpoints
USERS_ENDPOINT = '/api/users' # GET, POST, PATCH, DELETE
EMAIL_VRF_SIGNATURE = '/api/users/verify/'
AUTH_ENDPOINT = '/api/auth' # GET, POST, DELETE
TASKS_ENDPOINT = '/api/tasks' # GET, POST, PATCH, DELETE
DASHBOARDS_ENDPOINT = '/api/dashboards' # GET, POST, PATCH, DELETE
DASHBOARD_INVITATION_SIGNATURE = '/api/dashboards/invitation/'
BUDGETS_ENDPOINT = '/api/budgets' # GET, POST, PATCH, DELETE
TRANSACTIONS_ENDPOINT = '/api/transactions' # GET, POST, PATCH, DELETE
HOME_ENDPOINT = '/' # GET

# regex
REGEX_EMAIL = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
REGEX_UID = r'^(?=[a-zA-Z0-9._]{6,64}$)(?!.*[_.]{2})[^_.].*[^_.]$'
REGEX_HASH = r'[0-9a-f]{64}'