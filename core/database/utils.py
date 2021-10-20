import os

def getDbUri():
    db_user = os.environ.get('DB_USER')
    db_pass = os.environ.get('DB_PASS')
    db_name = os.environ.get('DB_NAME')
    db_host = os.environ.get('DB_HOST')

    host_args = db_host.split(":")
    if len(host_args) == 1:
        db_hostname = db_host
        db_port = os.environ.get("DB_PORT")
    elif len(host_args) == 2:
        db_hostname, db_port = host_args[0], int(host_args[1])

    URI = '{}://{}:{}@{}:{}/{}'.format(
            "postgresql+pg8000",
            db_user,
            db_pass,
            db_hostname,
            db_port,
            db_name)
    return URI