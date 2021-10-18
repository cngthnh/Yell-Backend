import os

def loadDbConfigs():
    try:
        os.environ['DB_USER'] = (open('db_user', 'r').readline()).strip()
        os.remove('db_user')
        os.environ['DB_PASS'] = (open('db_pass', 'r').readline()).strip()
        os.remove('db_pass')
        os.environ['DB_NAME'] = (open('db_name', 'r').readline()).strip()
        os.remove('db_name')
        os.environ['DB_HOST'] = (open('db_host', 'r').readline()).strip()
        os.remove('db_host')
    except Exception:
        pass

def loadKeys():
    try:
        os.environ['YELL_ENC_KEY'] = open('enc','r').readline().strip()
        os.remove('enc')
        os.environ['YELL_SIG_KEY'] = open('sig','r').readline().strip()
        os.remove('sig')
    except Exception:
        pass

def loadEmailConfigs():
    try:
        os.environ['MAIL_USERNAME'] = (open('mail_username', 'r').readline()).strip()
        os.remove('mail_username')
        os.environ['MAIL_PASSWORD'] = (open('mail_password', 'r').readline()).strip()
        os.remove('mail_password')
    except Exception:
        pass

def loadUrl():
    try:
        os.environ['YELL_MAIN_URL'] = (open('main_url', 'r').readline()).strip()
        os.remove('main_url')
    except Exception:
        pass

def loadConfigs():
    loadDbConfigs()
    loadEmailConfigs()
    loadKeys()
    loadUrl()